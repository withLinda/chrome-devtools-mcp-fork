#!/usr/bin/env python3
"""Storage Management Tools

This module provides browser storage management through the Chrome DevTools Protocol.
It enables inspection and manipulation of cookies, local storage, session storage,
IndexedDB, and cache storage across different origins.

Key Features:
    - Storage usage and quota monitoring
    - Cookie management (read, write, delete)
    - Storage clearing by type and origin
    - IndexedDB and Cache Storage tracking
    - Cross-origin storage inspection

Example:
    Managing browser storage and cookies:

    ```python
    # Check storage usage for an origin
    usage = await get_storage_usage_and_quota('https://example.com')

    # Clear specific storage types
    await clear_storage_for_origin('https://example.com', 'cookies,local_storage')

    # Manage cookies
    cookies = await get_all_cookies()
    await set_cookie(name='session', value='abc123', domain='.example.com')
    await clear_all_cookies()

    # Track storage changes
    await track_indexeddb('https://example.com', enable=True)
    await override_storage_quota('https://example.com', quota_size_mb=100)
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
    from .utils import create_error_response, create_success_response
except ImportError:
    try:
        from chrome_devtools_mcp_fork.tools.utils import create_error_response, create_success_response
    except ImportError:
        from utils import create_error_response, create_success_response


def register_storage_tools(mcp: FastMCP) -> None:
    """Register storage management tools with the MCP server."""

    @mcp.tool()
    @require_cdp_client
    async def get_storage_usage_and_quota(origin: str, **kwargs: Any) -> dict[str, Any]:
        """
        Get storage usage and quota information for an origin.

        Args:
            origin: Security origin to check storage for

        Returns:
            Storage usage and quota information in bytes
        """
        try:
            cdp_client = kwargs["cdp_client"]
            result = await cdp_client.send_command("Storage.getUsageAndQuota", {"origin": origin})

            usage_breakdown = {}
            if result.get("usageBreakdown"):
                for item in result["usageBreakdown"]:
                    storage_type = item.get("storageType", "unknown")
                    usage = item.get("usage", 0)
                    usage_breakdown[storage_type] = usage

            quota_mb = result["quota"] / (1024 * 1024) if result.get("quota") else 0
            usage_mb = result["usage"] / (1024 * 1024) if result.get("usage") else 0
            usage_percentage = (
                (result["usage"] / result["quota"] * 100) if result.get("quota", 0) > 0 else 0
            )

            return create_success_response(
                message=f"Retrieved storage usage for origin: {origin}",
                data={
                    "origin": origin,
                    "usageBytes": result.get("usage", 0),
                    "quotaBytes": result.get("quota", 0),
                    "usageMB": round(usage_mb, 2),
                    "quotaMB": round(quota_mb, 2),
                    "usagePercentage": round(usage_percentage, 2),
                    "overrideActive": result.get("overrideActive", False),
                    "usageBreakdown": usage_breakdown,
                },
            )

        except Exception as e:
            return create_error_response(f"Error getting storage usage and quota: {e}")

    @mcp.tool()
    @require_cdp_client
    async def clear_storage_for_origin(
        origin: str, storage_types: str = "all", **kwargs: Any
    ) -> dict[str, Any]:
        """
        Clear storage data for a specific origin.

        Args:
            origin: Security origin to clear storage for
            storage_types: Comma-separated list of storage types to clear
                          (cookies, local_storage, indexeddb, cache_storage, etc.)

        Returns:
            Success status of the clear operation
        """
        try:
            cdp_client = kwargs["cdp_client"]
            await cdp_client.send_command(
                "Storage.clearDataForOrigin", {"origin": origin, "storageTypes": storage_types}
            )

            return create_success_response(
                message=f"Cleared storage types '{storage_types}' for origin: {origin}",
                data={"origin": origin, "storageTypes": storage_types.split(","), "cleared": True},
            )

        except Exception as e:
            return create_error_response(f"Error clearing storage for origin: {e}")

    @mcp.tool()
    @require_cdp_client
    async def get_all_cookies(**kwargs: Any) -> dict[str, Any]:
        """
        Get all browser cookies.

        Returns:
            List of all cookies with details
        """
        try:
            cdp_client = kwargs["cdp_client"]
            result = await cdp_client.send_command("Storage.getCookies")

            cookies = result.get("cookies", [])
            cookie_data = []

            for cookie in cookies:
                cookie_data.append(
                    {
                        "name": cookie.get("name"),
                        "value": cookie.get("value"),
                        "domain": cookie.get("domain"),
                        "path": cookie.get("path"),
                        "expires": cookie.get("expires"),
                        "httpOnly": cookie.get("httpOnly", False),
                        "secure": cookie.get("secure", False),
                        "sameSite": cookie.get("sameSite"),
                        "size": cookie.get("size", 0),
                    }
                )

            domains: dict[str, list[str]] = {}
            for cookie in cookie_data:
                domain = cookie["domain"]
                if domain not in domains:
                    domains[domain] = []
                domains[domain].append(cookie["name"])

            return create_success_response(
                message=f"Retrieved {len(cookie_data)} cookies",
                data={
                    "cookies": cookie_data,
                    "totalCount": len(cookie_data),
                    "domains": domains,
                    "domainCount": len(domains),
                },
            )

        except Exception as e:
            return create_error_response(f"Error getting cookies: {e}")

    @mcp.tool()
    @require_cdp_client
    async def clear_all_cookies(**kwargs: Any) -> dict[str, Any]:
        """
        Clear all browser cookies.

        Returns:
            Success status of the clear operation
        """
        try:
            cdp_client = kwargs["cdp_client"]
            await cdp_client.send_command("Storage.clearCookies")

            return create_success_response(
                message="Cleared all browser cookies", data={"cleared": True, "type": "cookies"}
            )

        except Exception as e:
            return create_error_response(f"Error clearing cookies: {e}")

    @mcp.tool()
    @require_cdp_client
    async def set_cookie(
        name: str,
        value: str,
        domain: str,
        path: str = "/",
        expires: float | None = None,
        http_only: bool = False,
        secure: bool = False,
        same_site: str = "Lax",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Set a browser cookie.

        Args:
            name: Cookie name
            value: Cookie value
            domain: Cookie domain
            path: Cookie path (default: "/")
            expires: Expiration timestamp (optional)
            http_only: HttpOnly flag
            secure: Secure flag
            same_site: SameSite policy (Strict, Lax, None)

        Returns:
            Success status of the set operation
        """
        try:
            cdp_client = kwargs["cdp_client"]
            cookie_data = {
                "name": name,
                "value": value,
                "domain": domain,
                "path": path,
                "httpOnly": http_only,
                "secure": secure,
                "sameSite": same_site,
            }

            if expires is not None:
                cookie_data["expires"] = expires

            await cdp_client.send_command("Storage.setCookies", {"cookies": [cookie_data]})

            return create_success_response(
                message=f"Set cookie '{name}' for domain '{domain}'",
                data={"cookie": cookie_data, "set": True},
            )

        except Exception as e:
            return create_error_response(f"Error setting cookie: {e}")

    @mcp.tool()
    @require_cdp_client
    async def get_storage_key_for_frame(frame_id: str, **kwargs: Any) -> dict[str, Any]:
        """
        Get the storage key for a specific frame.

        Args:
            frame_id: Frame ID to get storage key for

        Returns:
            Storage key for the frame
        """
        try:
            cdp_client = kwargs["cdp_client"]
            result = await cdp_client.send_command(
                "Storage.getStorageKeyForFrame", {"frameId": frame_id}
            )

            return create_success_response(
                message=f"Retrieved storage key for frame {frame_id}",
                data={"frameId": frame_id, "storageKey": result["storageKey"]},
            )

        except Exception as e:
            return create_error_response(f"Error getting storage key for frame: {e}")

    @mcp.tool()
    @require_cdp_client
    async def track_cache_storage(
        origin: str, enable: bool = True, **kwargs: Any
    ) -> dict[str, Any]:
        """
        Enable or disable cache storage tracking for an origin.

        Args:
            origin: Security origin to track
            enable: Whether to enable or disable tracking

        Returns:
            Tracking status
        """
        try:
            cdp_client = kwargs["cdp_client"]
            if enable:
                await cdp_client.send_command(
                    "Storage.trackCacheStorageForOrigin", {"origin": origin}
                )
                message = f"Started tracking cache storage for origin: {origin}"
            else:
                await cdp_client.send_command(
                    "Storage.untrackCacheStorageForOrigin", {"origin": origin}
                )
                message = f"Stopped tracking cache storage for origin: {origin}"

            return create_success_response(
                message=message,
                data={"origin": origin, "tracking": enable, "storageType": "cache_storage"},
            )

        except Exception as e:
            return create_error_response(f"Error managing cache storage tracking: {e}")

    @mcp.tool()
    @require_cdp_client
    async def track_indexeddb(origin: str, enable: bool = True, **kwargs: Any) -> dict[str, Any]:
        """
        Enable or disable IndexedDB tracking for an origin.

        Args:
            origin: Security origin to track
            enable: Whether to enable or disable tracking

        Returns:
            Tracking status
        """
        try:
            cdp_client = kwargs["cdp_client"]
            if enable:
                await cdp_client.send_command("Storage.trackIndexedDBForOrigin", {"origin": origin})
                message = f"Started tracking IndexedDB for origin: {origin}"
            else:
                await cdp_client.send_command(
                    "Storage.untrackIndexedDBForOrigin", {"origin": origin}
                )
                message = f"Stopped tracking IndexedDB for origin: {origin}"

            return create_success_response(
                message=message,
                data={"origin": origin, "tracking": enable, "storageType": "indexeddb"},
            )

        except Exception as e:
            return create_error_response(f"Error managing IndexedDB tracking: {e}")

    @mcp.tool()
    @require_cdp_client
    async def override_storage_quota(
        origin: str, quota_size_mb: float | None = None, **kwargs: Any
    ) -> dict[str, Any]:
        """
        Override storage quota for a specific origin.

        Args:
            origin: Security origin to override quota for
            quota_size_mb: New quota size in MB (optional, removes override if not provided)

        Returns:
            Quota override status
        """
        try:
            cdp_client = kwargs["cdp_client"]
            params: dict[str, Any] = {"origin": origin}
            if quota_size_mb is not None:
                params["quotaSize"] = int(quota_size_mb * 1024 * 1024)

            await cdp_client.send_command("Storage.overrideQuotaForOrigin", params)

            if quota_size_mb is not None:
                message = f"Set storage quota override to {quota_size_mb}MB for origin: {origin}"
            else:
                message = f"Removed storage quota override for origin: {origin}"

            return create_success_response(
                message=message,
                data={
                    "origin": origin,
                    "quotaSizeMB": quota_size_mb,
                    "overrideActive": quota_size_mb is not None,
                },
            )

        except Exception as e:
            return create_error_response(f"Error overriding storage quota: {e}")
