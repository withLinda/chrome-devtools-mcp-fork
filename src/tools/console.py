#!/usr/bin/env python3
"""Console Tools

This module provides browser console interaction through the DevTools Protocol.
It enables JavaScript execution, console log monitoring, error tracking, and object inspection
within the connected Chrome browser instance.

The tools support real-time console monitoring, detailed error analysis, and interactive
JavaScript evaluation with complete error handling and response formatting. All operations
integrate seamlessly with Chrome's Runtime and Console domains.

Key Features:
    - Real-time console log capture and filtering
    - JavaScript code execution with error handling
    - Console object inspection and property analysis
    - Error and warning categorisation and summarisation
    - Live console monitoring with configurable duration
    - Console clearing and management operations

Example:
    Executing JavaScript and monitoring console:

    ```python
    # Execute JavaScript code
    result = await execute_javascript('console.log("Hello World")')

    # Get recent console logs
    logs = await get_console_logs(level='error', limit=10)

    # Monitor console for 30 seconds
    monitoring = await monitor_console_live(duration_seconds=30)
    ```

Note:
    All console operations require an active connection to Chrome. The module automatically
    handles timestamp conversion and data sanitisation for consistent response formatting.
"""

from __future__ import annotations

import asyncio
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..cdp_context import require_cdp_client
from .utils import create_error_response, create_success_response, safe_timestamp_conversion


def register_console_tools(mcp: FastMCP) -> None:
    """Register comprehensive console interaction tools with the MCP server.

    Adds all browser console management functions as MCP tools, providing complete
    JavaScript execution capabilities, console monitoring, and debugging support.
    Each tool includes robust error handling and standardised response formatting.

    The registered tools support the full range of console operations:
    - Console log retrieval with filtering and categorisation
    - JavaScript code execution with detailed error reporting
    - Object inspection and property analysis
    - Real-time console monitoring and live tracking
    - Console management operations (clearing, etc.)

    Args:
        mcp: FastMCP server instance to register tools with. Must be properly
             initialised before calling this function.

    Registered Tools:
        - get_console_logs: Retrieve and filter console messages
        - get_console_error_summary: Categorised error and warning analysis
        - execute_javascript: Run JavaScript code in browser context
        - clear_console: Clear browser console entries
        - inspect_console_object: Detailed object property inspection
        - monitor_console_live: Real-time console monitoring

    Note:
        All tools require access to the global CDP client instance and active
        browser connection for operation. Tools will return appropriate error
        responses if the client is unavailable or disconnected.
    """

    @mcp.tool()
    @require_cdp_client
    async def get_console_logs(
        cdp_client, level: str | None = None, limit: int | None = None
    ) -> dict[str, Any]:
        """
        Get browser console logs with optional filtering.

        Args:
            level: Filter by log level (log, warn, error, info, debug)
            limit: Maximum number of logs to return

        Returns:
            List of console logs matching the criteria
        """
        try:
            logs = cdp_client.console_logs.copy()

            if level:
                logs = [log for log in logs if log.get("type") == level]

            if limit:
                logs = logs[:limit]

            for log in logs:
                if "timestamp" in log:
                    log["timestamp"] = safe_timestamp_conversion(log["timestamp"])

            return create_success_response(
                message=f"Retrieved {len(logs)} console logs",
                data={
                    "logs": logs,
                    "totalCount": len(cdp_client.console_logs),
                    "filteredCount": len(logs),
                    "filters": {"level": level, "limit": limit},
                },
            )

        except Exception as e:
            return create_error_response(f"Error retrieving console logs: {e}")

    @mcp.tool()
    @require_cdp_client
    async def get_console_error_summary(cdp_client) -> dict[str, Any]:
        """
        Get an organised summary of console errors and warnings.

        Returns:
            Categorised summary of console errors and warnings
        """
        try:
            logs = cdp_client.console_logs

            errors = [log for log in logs if log.get("type") == "error"]
            warnings = [log for log in logs if log.get("type") == "warning"]

            error_groups: dict[str, list[dict[str, Any]]] = {}
            for error in errors:
                message = str(error.get("args", ["Unknown error"])[0])
                if message not in error_groups:
                    error_groups[message] = []
                error_groups[message].append(error)

            warning_groups: dict[str, list[dict[str, Any]]] = {}
            for warning in warnings:
                message = str(warning.get("args", ["Unknown warning"])[0])
                if message not in warning_groups:
                    warning_groups[message] = []
                warning_groups[message].append(warning)

            return create_success_response(
                message=f"Console summary: {len(errors)} errors, {len(warnings)} warnings",
                data={
                    "errorCount": len(errors),
                    "warningCount": len(warnings),
                    "errorGroups": {
                        msg: {"count": len(group), "examples": group[:3]}
                        for msg, group in error_groups.items()
                    },
                    "warningGroups": {
                        msg: {"count": len(group), "examples": group[:3]}
                        for msg, group in warning_groups.items()
                    },
                    "recentErrors": errors[-5:] if errors else [],
                    "recentWarnings": warnings[-5:] if warnings else [],
                },
            )

        except Exception as e:
            return create_error_response(f"Error creating console summary: {e}")

    @mcp.tool()
    @require_cdp_client
    async def execute_javascript(cdp_client, code: str) -> dict[str, Any]:
        """
        Execute JavaScript code in the browser context.

        Args:
            code: JavaScript code to execute

        Returns:
            Result of the JavaScript execution
        """
        try:
            result = await cdp_client.send_command(
                "Runtime.evaluate",
                {"expression": code, "returnByValue": True, "awaitPromise": True},
            )

            if result.get("exceptionDetails"):
                exception = result["exceptionDetails"]
                return create_error_response(
                    "JavaScript execution failed",
                    details=exception.get("text", "Unknown error"),
                    data={"code": code, "exception": exception},
                )

            return create_success_response(
                message="JavaScript executed successfully",
                data={
                    "code": code,
                    "result": result.get("result", {}),
                    "value": result.get("result", {}).get("value"),
                    "type": result.get("result", {}).get("type"),
                },
            )

        except Exception as e:
            return create_error_response(f"Error executing JavaScript: {e}")

    @mcp.tool()
    @require_cdp_client
    async def clear_console(cdp_client) -> dict[str, Any]:
        """
        Clear the browser console.

        Returns:
            Status of the clear operation
        """
        try:
            await cdp_client.send_command("Runtime.discardConsoleEntries")

            cdp_client.console_logs.clear()

            return create_success_response(
                message="Console cleared successfully", data={"cleared": True}
            )

        except Exception as e:
            return create_error_response(f"Error clearing console: {e}")

    @mcp.tool()
    @require_cdp_client
    async def inspect_console_object(cdp_client, expression: str) -> dict[str, Any]:
        """
        Inspect a JavaScript object or expression in detail.

        Args:
            expression: JavaScript expression to inspect

        Returns:
            Detailed object inspection results
        """
        try:
            result = await cdp_client.send_command(
                "Runtime.evaluate", {"expression": expression, "returnByValue": False}
            )

            if result.get("exceptionDetails"):
                return create_error_response(
                    f"Failed to evaluate expression: {expression}",
                    details=result["exceptionDetails"].get("text"),
                )

            object_id = result.get("result", {}).get("objectId")
            if not object_id:
                return create_success_response(
                    message=f"Inspected expression: {expression}",
                    data={
                        "expression": expression,
                        "result": result.get("result", {}),
                        "type": "primitive",
                    },
                )

            props_result = await cdp_client.send_command(
                "Runtime.getProperties", {"objectId": object_id, "ownProperties": True}
            )

            properties = {}
            for prop in props_result.get("result", []):
                prop_name = prop.get("name")
                prop_value = prop.get("value", {})
                properties[prop_name] = {
                    "type": prop_value.get("type"),
                    "value": prop_value.get("value"),
                    "description": prop_value.get("description"),
                }

            return create_success_response(
                message=f"Inspected object: {expression}",
                data={
                    "expression": expression,
                    "objectType": result.get("result", {}).get("type"),
                    "className": result.get("result", {}).get("className"),
                    "description": result.get("result", {}).get("description"),
                    "properties": properties,
                    "propertyCount": len(properties),
                },
            )

        except Exception as e:
            return create_error_response(f"Error inspecting object: {e}")

    @mcp.tool()
    @require_cdp_client
    async def monitor_console_live(cdp_client, duration_seconds: int = 10) -> dict[str, Any]:
        """
        Monitor console output in real-time for a specified duration.

        Args:
            duration_seconds: How long to monitor (default: 10 seconds)

        Returns:
            Console messages captured during monitoring period
        """
        try:
            initial_count = len(cdp_client.console_logs)

            await asyncio.sleep(duration_seconds)
            new_messages = cdp_client.console_logs[initial_count:]

            return create_success_response(
                message=f"Monitored console for {duration_seconds} seconds",
                data={
                    "duration": duration_seconds,
                    "newMessages": new_messages,
                    "messageCount": len(new_messages),
                    "initialCount": initial_count,
                    "finalCount": len(cdp_client.console_logs),
                },
            )

        except Exception as e:
            return create_error_response(f"Error monitoring console: {e}")
