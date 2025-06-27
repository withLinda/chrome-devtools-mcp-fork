#!/usr/bin/env python3
"""
Chrome DevTools Protocol Context Manager

This module provides a clean, elegant way to access the CDP client throughout
the application. It uses a context-based approach that eliminates repetitive
imports and connection checking whilst maintaining proper error handling.

The context manager ensures that:
- CDP client is properly initialised and connected
- Connection status is validated before operations
- Clear error messages are provided when client is unavailable
- Tools can focus on their core functionality rather than connection management

Example:
    ```python
    from .cdp_context import require_cdp_client

    @require_cdp_client
    async def my_tool_function(cdp_client):
        # CDP client is guaranteed to be connected
        result = await cdp_client.send_command("Page.navigate", {"url": "https://example.com"})
        return result
    ```
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, TypeVar

from .tools.utils import create_error_response

# Type variable for decorated functions
F = TypeVar("F", bound=Callable[..., Awaitable[Any]])


def require_cdp_client(func: F) -> Callable[..., Awaitable[Any]]:
    """
    Decorator that provides CDP client to tool functions with automatic validation.

    This decorator eliminates the need for repetitive client access and connection
    checking in every tool function. It automatically:

    1. Imports the CDP client from the main module
    2. Validates that the client exists and is connected
    3. Passes the validated client as the first parameter to the decorated function
    4. Returns appropriate error responses if client is unavailable

    Args:
        func: The async function to decorate. Must accept cdp_client as first parameter.

    Returns:
        The decorated function with automatic CDP client injection.

    Example:
        ```python
        @require_cdp_client
        async def get_page_title(cdp_client, **kwargs):
            result = await cdp_client.send_command("Runtime.evaluate", {
                "expression": "document.title",
                "returnByValue": True
            })
            return {"title": result["result"]["value"]}
        ```
    """

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            # Import CDP client dynamically to avoid circular imports
            from . import main

            cdp_client = main.cdp_client

            # Validate client availability and connection status
            if not cdp_client:
                return create_error_response(
                    "CDP client not initialised. Please start Chrome first."
                )

            if not cdp_client.connected:
                return create_error_response(
                    "Not connected to browser. Please connect to Chrome first."
                )

            # Call the original function with CDP client as first argument
            return await func(cdp_client, *args, **kwargs)

        except ImportError:
            return create_error_response(
                "CDP client module not available. Please check server configuration."
            )
        except Exception as e:
            return create_error_response(f"CDP context error: {str(e)}")

    return wrapper  # type: ignore[return-value]


class CDPContext:
    """
    Context manager for Chrome DevTools Protocol operations.

    Provides a more explicit context-based approach for operations that require
    multiple CDP interactions. This is useful for complex operations that need
    to ensure the connection remains stable throughout the operation.

    Example:
        ```python
        async with CDPContext() as cdp:
            await cdp.send_command("Page.enable")
            await cdp.send_command("DOM.enable")
            result = await cdp.send_command("DOM.getDocument")
        ```
    """

    def __init__(self) -> None:
        """Initialise the CDP context manager."""
        self.cdp_client: Any = None

    async def __aenter__(self) -> Any:
        """
        Enter the async context and validate CDP client.

        Returns:
            The validated CDP client instance.

        Raises:
            RuntimeError: If CDP client is not available or not connected.
        """
        try:
            from . import main

            self.cdp_client = main.cdp_client

            if not self.cdp_client:
                raise RuntimeError("CDP client not initialised. Please start Chrome first.")

            if not self.cdp_client.connected:
                raise RuntimeError("Not connected to browser. Please connect to Chrome first.")

            return self.cdp_client

        except ImportError as e:
            raise RuntimeError("CDP client module not available.") from e

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """
        Exit the async context.

        Currently performs no cleanup, but provides a hook for future
        connection management improvements.
        """
        pass


def get_cdp_client() -> Any:
    """
    Get the current CDP client instance without validation.

    This function provides direct access to the CDP client for cases where
    you need to check its status or perform conditional operations based on
    availability.

    Returns:
        ChromeDevToolsClient | None: The CDP client instance or None if not available.

    Example:
        ```python
        cdp = get_cdp_client()
        if cdp and cdp.connected:
            # Perform operation
            result = await cdp.send_command("Page.getNavigationHistory")
        ```
    """
    try:
        from . import main
        return main.cdp_client
    except ImportError:
        return None
