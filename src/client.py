#!/usr/bin/env python3
"""Chrome DevTools Protocol Client

This module contains the ChromeDevToolsClient class that manages WebSocket connections
to Chrome's remote debugging interface and handles CDP commands and events.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from collections.abc import Callable
from typing import Any

import aiohttp
import websockets

logger = logging.getLogger(__name__)


class ChromeDevToolsClient:
    """
    Chrome DevTools Protocol client with WebSocket communication capabilities.

    This class manages the connection to Chrome's remote debugging interface,
    handles event processing, and executes CDP commands. It maintains state
    for network requests and console logs, and provides a robust interface
    for web application debugging.

    The client automatically discovers available Chrome targets and establishes
    WebSocket connections for real-time communication with the browser.

    Attributes:
        port: Chrome remote debugging port (default: 9222)
        host: Hostname for Chrome connection (default: localhost)
        ws: WebSocket connection to Chrome DevTools
        connected: Connection status flag
        message_id: Incremental ID for CDP messages
        pending_messages: Awaiting responses for sent commands
        event_handlers: Registered handlers for CDP events
        network_requests: Captured network request data
        console_logs: Captured console log entries
    """

    def __init__(self, port: int = 9222, host: str = "localhost") -> None:
        """
        Initialise the Chrome DevTools Protocol client.

        Args:
            port: Chrome remote debugging port (overridden by CHROME_DEBUG_PORT env var)
            host: Hostname for Chrome connection
        """
        # Use environment variable if available for flexible configuration
        env_port = os.getenv("CHROME_DEBUG_PORT")
        if env_port and env_port.isdigit():
            port = int(env_port)

        self.port = port
        self.host = host
        self.ws: websockets.WebSocketServerProtocol | None = None  # type: ignore
        self.connected = False
        self.message_id = 0
        self.pending_messages: dict[int, asyncio.Future] = {}
        self.event_handlers: dict[str, list[Callable[[dict[str, Any]], None]]] = {}

        # Storage for captured browser data
        self.network_requests: list[dict[str, Any]] = []
        self.console_logs: list[dict[str, Any]] = []

    async def connect(self) -> bool:
        """
        Establish connection to Chrome DevTools via WebSocket.

        Discovers available Chrome targets and connects to the first available
        target using WebSocket communication. Starts the message handling loop
        for processing incoming CDP events and responses.

        Returns:
            bool: True if connection successful, False otherwise

        Raises:
            ConnectionError: If no browser targets are available
        """
        try:
            targets = await self._get_available_targets()
            if not targets:
                raise ConnectionError("No browser targets available")

            target = targets[0]
            ws_url = target["webSocketDebuggerUrl"]

            self.ws = await websockets.connect(ws_url)
            self.connected = True

            asyncio.create_task(self._handle_incoming_messages())

            logger.info(f"Connected to Chrome target: {target.get('title', 'Unknown')}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Chrome: {e}")
            self.connected = False
            return False

    async def disconnect(self) -> None:
        """Gracefully disconnect from Chrome DevTools."""
        if self.ws:
            await self.ws.close()
        self.connected = False
        self.ws = None
        logger.info("Disconnected from Chrome")

    async def _get_available_targets(self) -> list[dict[str, Any]]:
        """Retrieve list of available Chrome targets."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://{self.host}:{self.port}/json") as response:
                    if response.status == 200:
                        targets = await response.json()
                        return [t for t in targets if t.get("type") == "page"]
                    return []
        except Exception as e:
            logger.error(f"Failed to get targets: {e}")
            return []

    async def send_command(
        self, method: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Send a command to Chrome DevTools and wait for response."""
        if not self.connected or not self.ws:
            raise ConnectionError("Not connected to Chrome")

        self.message_id += 1
        message = {"id": self.message_id, "method": method, "params": params or {}}

        future: asyncio.Future[dict[str, Any]] = asyncio.Future()
        self.pending_messages[self.message_id] = future

        try:
            await self.ws.send(json.dumps(message))
            result = await asyncio.wait_for(future, timeout=10.0)
            return result  # type: ignore
        except asyncio.TimeoutError:
            if self.message_id in self.pending_messages:
                del self.pending_messages[self.message_id]
            raise TimeoutError(f"Command {method} timed out") from None
        except Exception as e:
            if self.message_id in self.pending_messages:
                del self.pending_messages[self.message_id]
            raise e

    async def _handle_incoming_messages(self) -> None:
        """Handle incoming WebSocket messages from Chrome."""
        try:
            if self.ws is not None:
                async for message in self.ws:
                    try:
                        data = json.loads(message)

                        if "id" in data:
                            message_id = data["id"]
                            if message_id in self.pending_messages:
                                future = self.pending_messages.pop(message_id)
                                if "error" in data:
                                    future.set_exception(Exception(data["error"]["message"]))
                                else:
                                    future.set_result(data.get("result", {}))

                        elif "method" in data:
                            await self._process_event(data)

                    except json.JSONDecodeError:
                        logger.warning("Received invalid JSON from Chrome")
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")

        except websockets.exceptions.ConnectionClosed:
            logger.info("Chrome connection closed")
            self.connected = False
        except Exception as e:
            logger.error(f"Error in message handler: {e}")
            self.connected = False

    async def _process_event(self, event: dict[str, Any]) -> None:
        """Process CDP event notifications and store relevant data."""
        method = event["method"]
        params = event.get("params", {})

        if method == "Network.requestWillBeSent":
            await self._process_network_request(params)
        elif method == "Network.responseReceived":
            await self._process_network_response(params)
        elif method == "Network.loadingFinished":
            await self._process_network_completion(params)
        elif method == "Network.loadingFailed":
            await self._process_network_failure(params)
        elif method == "Runtime.consoleAPICalled":
            await self._process_console_message(params)
        elif method == "Runtime.exceptionThrown":
            await self._process_console_exception(params)

        if method in self.event_handlers:
            for handler in self.event_handlers[method]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(params)
                    else:
                        handler(params)
                except Exception as e:
                    logger.error(f"Error in event handler for {method}: {e}")

    async def _process_network_request(self, params: dict[str, Any]) -> None:
        """Process network request event."""
        from .tools.utils import safe_timestamp_conversion

        self.network_requests.append(
            {
                "requestId": params["requestId"],
                "url": params["request"]["url"],
                "method": params["request"]["method"],
                "headers": params["request"].get("headers", {}),
                "timestamp": safe_timestamp_conversion(params["timestamp"]),
                "type": "request",
                "status": "pending",
            }
        )

    async def _process_network_response(self, params: dict[str, Any]) -> None:
        """Process network response event."""
        from .tools.utils import safe_timestamp_conversion

        request_id = params["requestId"]
        for req in self.network_requests:
            if req.get("requestId") == request_id and req["type"] == "request":
                req.update(
                    {
                        "response": {
                            "status": params["response"]["status"],
                            "statusText": params["response"]["statusText"],
                            "headers": params["response"]["headers"],
                            "mimeType": params["response"]["mimeType"],
                            "timestamp": safe_timestamp_conversion(params["timestamp"]),
                            "remoteIPAddress": params["response"].get("remoteIPAddress"),
                            "protocol": params["response"].get("protocol"),
                        },
                        "status": "responded",
                    }
                )
                break

    async def _process_network_completion(self, params: dict[str, Any]) -> None:
        """Process network loading completion event."""
        request_id = params["requestId"]
        for req in self.network_requests:
            if req.get("requestId") == request_id:
                req.update(
                    {"status": "completed", "encodedDataLength": params.get("encodedDataLength")}
                )
                break

    async def _process_network_failure(self, params: dict[str, Any]) -> None:
        """Process network loading failure event."""
        request_id = params["requestId"]
        for req in self.network_requests:
            if req.get("requestId") == request_id:
                req.update(
                    {
                        "status": "failed",
                        "errorText": params.get("errorText"),
                        "cancelled": params.get("canceled", False),
                    }
                )
                break

    async def _process_console_message(self, params: dict[str, Any]) -> None:
        """Process console API call event."""
        from .tools.utils import safe_timestamp_conversion

        self.console_logs.append(
            {
                "type": params["type"],
                "args": [arg.get("value", str(arg)) for arg in params["args"]],
                "timestamp": safe_timestamp_conversion(params["timestamp"]),
                "executionContextId": params.get("executionContextId"),
                "stackTrace": params.get("stackTrace"),
            }
        )

    async def _process_console_exception(self, params: dict[str, Any]) -> None:
        """Process console exception event."""
        from .tools.utils import safe_timestamp_conversion

        exception = params["exceptionDetails"]
        self.console_logs.append(
            {
                "type": "error",
                "args": [exception.get("text", "Unknown error")],
                "timestamp": safe_timestamp_conversion(params["timestamp"]),
                "executionContextId": exception.get("executionContextId"),
                "stackTrace": exception.get("stackTrace"),
                "exception": True,
            }
        )

    async def enable_domains(self) -> None:
        """Enable necessary CDP domains for functionality."""
        domains = [
            "Network",
            "Runtime",
            "Page",
            "Performance",
            "DOM",
            "CSS",
            "Security",
            "DOMStorage",
        ]
        for domain in domains:
            try:
                await self.send_command(f"{domain}.enable")
                logger.info(f"{domain} domain enabled")
            except Exception as e:
                logger.warning(f"Failed to enable {domain} domain: {e}")

    async def get_target_info(self) -> dict[str, Any]:
        """Get information about the current target."""
        try:
            return await self.send_command("Target.getTargetInfo")
        except Exception:
            return {"title": "Unknown", "url": "Unknown"}

    def add_event_handler(
        self, event_method: str, handler: Callable[[dict[str, Any]], None]
    ) -> None:
        """Register an event handler for a specific CDP event."""
        if event_method not in self.event_handlers:
            self.event_handlers[event_method] = []
        self.event_handlers[event_method].append(handler)
