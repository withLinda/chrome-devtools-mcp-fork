#!/usr/bin/env python3
"""Network Monitoring Tools

This module provides network request monitoring and analysis through the Chrome DevTools Protocol.
It captures HTTP requests and responses, allowing filtering and detailed inspection of network
traffic during browser sessions.

Key Features:
    - Real-time network request capture
    - Request filtering by domain and status code
    - Response body retrieval and analysis
    - Request/response header inspection

Example:
    Monitoring network requests and analyzing responses:

    ```python
    # Get all network requests
    requests = await get_network_requests()

    # Filter requests by domain
    api_requests = await get_network_requests(filter_domain='api.example.com')

    # Get failed requests only
    errors = await get_network_requests(filter_status=404, limit=10)

    # Get detailed response data
    response = await get_network_response(request_id='12345')
    ```
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

try:
    from ..cdp_context import require_cdp_client
except ImportError:
    try:
        from chrome_devtools_mcp_fork.cdp_context import require_cdp_client
    except ImportError:
        import os
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from cdp_context import require_cdp_client
try:
    from .utils import create_error_response, create_success_response, safe_timestamp_conversion
except ImportError:
    try:
        from chrome_devtools_mcp_fork.tools.utils import create_error_response, create_success_response, safe_timestamp_conversion
    except ImportError:
        from utils import create_error_response, create_success_response, safe_timestamp_conversion


def register_network_tools(mcp: FastMCP) -> None:
    """Register network monitoring tools with the MCP server."""

    @mcp.tool()
    @require_cdp_client
    async def get_network_requests(
        filter_domain: str | None = None,
        filter_status: int | None = None,
        limit: int | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Get captured network requests with optional filtering.

        Args:
            filter_domain: Filter by domain (optional)
            filter_status: Filter by HTTP status code (optional)
            limit: Maximum number of requests to return (optional)

        Returns:
            List of network requests matching the criteria
        """
        try:
            cdp_client = kwargs["cdp_client"]
            requests = cdp_client.network_requests.copy()

            if filter_domain:
                requests = [
                    req for req in requests if filter_domain.lower() in req.get("url", "").lower()
                ]

            if filter_status:
                requests = [
                    req
                    for req in requests
                    if req.get("response", {}).get("status") == filter_status
                ]

            if limit:
                requests = requests[:limit]

            for req in requests:
                if "timestamp" in req:
                    req["timestamp"] = safe_timestamp_conversion(req["timestamp"])
                if "response" in req and "timestamp" in req["response"]:
                    req["response"]["timestamp"] = safe_timestamp_conversion(
                        req["response"]["timestamp"]
                    )

            return create_success_response(
                message=f"Retrieved {len(requests)} network requests",
                data={
                    "requests": requests,
                    "totalCount": len(cdp_client.network_requests),
                    "filteredCount": len(requests),
                    "filters": {"domain": filter_domain, "status": filter_status, "limit": limit},
                },
            )

        except Exception as e:
            return create_error_response(f"Error retrieving network requests: {e}")

    @mcp.tool()
    @require_cdp_client
    async def get_network_response(request_id: str, **kwargs: Any) -> dict[str, Any]:
        """
        Get detailed response data for a specific network request.

        Args:
            request_id: ID of the network request

        Returns:
            Detailed response data including body content
        """
        try:
            cdp_client = kwargs["cdp_client"]
            result = await cdp_client.send_command(
                "Network.getResponseBody", {"requestId": request_id}
            )

            request_data = None
            for req in cdp_client.network_requests:
                if req.get("requestId") == request_id:
                    request_data = req
                    break

            if not request_data:
                return create_error_response(f"Request ID {request_id} not found")

            response_data = {
                "requestId": request_id,
                "url": request_data.get("url"),
                "method": request_data.get("method"),
                "status": request_data.get("response", {}).get("status"),
                "statusText": request_data.get("response", {}).get("statusText"),
                "headers": request_data.get("response", {}).get("headers", {}),
                "mimeType": request_data.get("response", {}).get("mimeType"),
                "body": result.get("body"),
                "base64Encoded": result.get("base64Encoded", False),
                "bodySize": len(result.get("body", "")),
                "timestamp": safe_timestamp_conversion(
                    request_data.get("response", {}).get("timestamp", 0)
                ),
            }

            return create_success_response(
                message=f"Retrieved response data for request {request_id}", data=response_data
            )

        except Exception as e:
            return create_error_response(f"Error getting network response: {e}")
