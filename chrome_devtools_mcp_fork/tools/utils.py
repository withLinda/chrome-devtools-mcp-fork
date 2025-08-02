#!/usr/bin/env python3
"""Shared Utilities

This module provides common utility functions used across all Chrome DevTools MCP tools.
It includes standardized response formatting, data sanitization for JSON serialization,
and timestamp conversion between Chrome and Python formats.

Key Features:
    - Standardized success/error response formatting
    - JSON-safe data sanitization
    - Chrome timestamp conversion
    - Consistent error handling patterns

Example:
    Using utility functions in tool implementations:

    ```python
    # Create standardized responses
    success = create_success_response(
        message="Element found",
        data={"nodeId": 123, "tagName": "div"}
    )

    # Handle errors consistently
    error = create_error_response(
        error="Element not found",
        details="No element matches selector '.missing'"
    )

    # Convert Chrome timestamps
    python_time = safe_timestamp_conversion(chrome_timestamp)
    ```
"""

from __future__ import annotations

import time
from typing import Any


def create_success_response(
    message: str = "Operation completed successfully", **kwargs: Any
) -> dict[str, Any]:
    """Create a standardised success response."""
    response = {"success": True, "message": message, "timestamp": time.time(), **kwargs}
    if kwargs.get("data") is not None:
        response["data"] = sanitise_data(kwargs["data"])
    return response


def create_error_response(
    error: str, details: str | None = None, **kwargs: Any
) -> dict[str, Any]:
    """Create a standardised error response."""
    response = {"success": False, "error": error, "timestamp": time.time(), **kwargs}
    if details:
        response["details"] = details
    if kwargs.get("data") is not None:
        response["data"] = sanitise_data(kwargs["data"])
    return response


def sanitise_data(data: Any) -> Any:
    """Sanitise data for JSON serialisation."""
    if isinstance(data, dict):
        return {k: sanitise_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitise_data(item) for item in data]
    elif isinstance(data, int | float | str | bool) or data is None:
        return data
    else:
        return str(data)


def safe_timestamp_conversion(timestamp: float) -> float:
    """Safely convert Chrome timestamps to Python timestamps."""
    try:
        # Chrome timestamps can be in microseconds (>1e10) or seconds
        if timestamp > 1e10:
            return timestamp / 1000
        return timestamp
    except (ValueError, TypeError):
        return time.time()
