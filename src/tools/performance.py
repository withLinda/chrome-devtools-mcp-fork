#!/usr/bin/env python3
"""Performance and Page Analysis Tools

This module provides performance monitoring and page analysis through the Chrome DevTools Protocol.
It captures runtime metrics, resource timing data, and page characteristics to help identify
performance bottlenecks and optimization opportunities.

Key Features:
    - Page load and runtime performance metrics
    - Resource timing and network performance data
    - DOM element counts and page structure analysis
    - JavaScript heap and memory usage monitoring
    - Frame timing and rendering performance

Example:
    Analyzing page performance and metrics:
    
    ```python
    # Get comprehensive page information
    page_info = await get_page_info()
    # Returns: title, URL, element counts, timing data
    
    # Get detailed performance metrics
    metrics = await get_performance_metrics()
    # Returns: FCP, LCP, CLS, resource timing, memory usage
    
    # Monitor cookies for performance impact
    cookies = await get_cookies(domain='example.com')
    
    # Execute code across all frames
    results = await evaluate_in_all_frames('window.location.href')
    ```
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ..cdp_context import require_cdp_client
from .utils import create_error_response, create_success_response


def register_performance_tools(mcp: FastMCP) -> None:
    """Register performance and page analysis tools with the MCP server."""

    @mcp.tool()
    @require_cdp_client
    async def get_page_info(cdp_client) -> dict[str, Any]:
        """
        Get comprehensive information about the current page.

        Returns:
            Page metrics, performance data, and element counts
        """
        try:
            page_info = {}

            basic_info_code = """
            ({
                title: document.title,
                url: window.location.href,
                readyState: document.readyState,
                referrer: document.referrer,
                lastModified: document.lastModified
            })
            """

            basic_result = await cdp_client.send_command(
                "Runtime.evaluate", {"expression": basic_info_code, "returnByValue": True}
            )
            page_info.update(basic_result["result"]["value"])

            metrics_code = """
            ({
                elements: {
                    scripts: document.scripts.length,
                    stylesheets: document.styleSheets.length,
                    images: document.images.length,
                    iframes: document.querySelectorAll('iframe').length,
                    forms: document.forms.length,
                    links: document.links.length
                },
                document: {
                    height: document.documentElement.scrollHeight,
                    width: document.documentElement.scrollWidth
                },
                viewport: {
                    height: window.innerHeight,
                    width: window.innerWidth
                },
                storage: {
                    localStorage: Object.keys(localStorage || {}).length,
                    sessionStorage: Object.keys(sessionStorage || {}).length
                }
            })
            """

            metrics_result = await cdp_client.send_command(
                "Runtime.evaluate", {"expression": metrics_code, "returnByValue": True}
            )
            page_info["metrics"] = metrics_result["result"]["value"]

            timing_code = """
            (() => {
                const perf = performance.timing;
                const navigation = performance.navigation;
                const now = performance.now();

                return {
                    navigation: {
                        type: navigation.type,
                        redirectCount: navigation.redirectCount
                    },
                    timing: {
                        navigationStart: perf.navigationStart,
                        domainLookupStart: perf.domainLookupStart,
                        domainLookupEnd: perf.domainLookupEnd,
                        connectStart: perf.connectStart,
                        connectEnd: perf.connectEnd,
                        requestStart: perf.requestStart,
                        responseStart: perf.responseStart,
                        responseEnd: perf.responseEnd,
                        domLoading: perf.domLoading,
                        domInteractive: perf.domInteractive,
                        domContentLoadedEventStart: perf.domContentLoadedEventStart,
                        domContentLoadedEventEnd: perf.domContentLoadedEventEnd,
                        domComplete: perf.domComplete,
                        loadEventStart: perf.loadEventStart,
                        loadEventEnd: perf.loadEventEnd
                    },
                    calculated: {
                        dnsLookup: perf.domainLookupEnd - perf.domainLookupStart,
                        tcpConnection: perf.connectEnd - perf.connectStart,
                        serverResponse: perf.responseEnd - perf.requestStart,
                        domProcessing: perf.domComplete - perf.domLoading,
                        totalLoadTime: perf.loadEventEnd - perf.navigationStart,
                        timeToInteractive: perf.domInteractive - perf.navigationStart,
                        timeToContentLoaded: perf.domContentLoadedEventEnd - perf.navigationStart
                    },
                    currentTime: now
                };
            })()
            """

            timing_result = await cdp_client.send_command(
                "Runtime.evaluate", {"expression": timing_code, "returnByValue": True}
            )
            page_info["performance"] = timing_result["result"]["value"]

            return create_success_response(
                message="Retrieved comprehensive page information", data=page_info
            )

        except Exception as e:
            return create_error_response(f"Error getting page info: {e}")

    @mcp.tool()
    @require_cdp_client
    async def get_performance_metrics(cdp_client) -> dict[str, Any]:
        """
        Get detailed performance metrics and resource timing.

        Returns:
            Comprehensive performance analysis
        """
        try:
            await cdp_client.send_command("Performance.enable")
            metrics_result = await cdp_client.send_command("Performance.getMetrics")
            metrics = {}
            for metric in metrics_result.get("metrics", []):
                metrics[metric["name"]] = metric["value"]

            resource_code = """
            (() => {
                const resources = performance.getEntriesByType('resource');
                return resources.map(resource => ({
                    name: resource.name,
                    type: resource.initiatorType,
                    duration: resource.duration,
                    size: resource.transferSize || resource.encodedBodySize || 0,
                    startTime: resource.startTime,
                    responseEnd: resource.responseEnd,
                    domainLookupTime: resource.domainLookupEnd - resource.domainLookupStart,
                    connectTime: resource.connectEnd - resource.connectStart,
                    requestTime: resource.responseStart - resource.requestStart,
                    responseTime: resource.responseEnd - resource.responseStart
                }));
            })()
            """

            resource_result = await cdp_client.send_command(
                "Runtime.evaluate", {"expression": resource_code, "returnByValue": True}
            )

            resources = resource_result["result"]["value"]

            total_size = sum(r.get("size", 0) for r in resources)
            resource_types = {}
            for resource in resources:
                res_type = resource.get("type", "other")
                if res_type not in resource_types:
                    resource_types[res_type] = {"count": 0, "size": 0, "totalTime": 0}
                resource_types[res_type]["count"] += 1
                resource_types[res_type]["size"] += resource.get("size", 0)
                resource_types[res_type]["totalTime"] += resource.get("duration", 0)

            memory_code = """
            (() => {
                if ('memory' in performance) {
                    return {
                        usedJSHeapSize: performance.memory.usedJSHeapSize,
                        totalJSHeapSize: performance.memory.totalJSHeapSize,
                        jsHeapSizeLimit: performance.memory.jsHeapSizeLimit
                    };
                }
                return null;
            })()
            """

            memory_result = await cdp_client.send_command(
                "Runtime.evaluate", {"expression": memory_code, "returnByValue": True}
            )

            memory_info = memory_result["result"]["value"]

            return create_success_response(
                message="Retrieved detailed performance metrics",
                data={
                    "metrics": metrics,
                    "resources": {
                        "total": len(resources),
                        "totalSize": total_size,
                        "totalSizeMB": round(total_size / (1024 * 1024), 2),
                        "byType": resource_types,
                        "details": resources[:20],  # Limit to first 20 for readability
                    },
                    "memory": memory_info,
                    "summary": {
                        "resourceCount": len(resources),
                        "totalTransferSize": total_size,
                        "averageResourceSize": round(total_size / len(resources), 2)
                        if resources
                        else 0,
                        "largestResource": max(resources, key=lambda x: x.get("size", 0))
                        if resources
                        else None,
                    },
                },
            )

        except Exception as e:
            return create_error_response(f"Error getting performance metrics: {e}")

    @mcp.tool()
    @require_cdp_client
    async def get_cookies(cdp_client, domain: str | None = None) -> dict[str, Any]:
        """
        Get browser cookies with optional domain filtering.

        Args:
            domain: Filter cookies by domain (optional)

        Returns:
            List of cookies matching the criteria
        """
        try:
            # Get all cookies first
            result = await cdp_client.send_command("Network.getAllCookies")

            cookies = result.get("cookies", [])

            # Apply domain filter
            if domain:
                cookies = [
                    cookie
                    for cookie in cookies
                    if domain.lower() in cookie.get("domain", "").lower()
                ]

            # Process cookies for better readability
            processed_cookies = []
            for cookie in cookies:
                processed_cookies.append(
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

            return create_success_response(
                message=f"Retrieved {len(processed_cookies)} cookies"
                + (f" for domain '{domain}'" if domain else ""),
                data={
                    "cookies": processed_cookies,
                    "totalCount": len(processed_cookies),
                    "domain": domain,
                },
            )

        except Exception as e:
            return create_error_response(f"Error getting cookies: {e}")

    @mcp.tool()
    @require_cdp_client
    async def evaluate_in_all_frames(cdp_client, code: str) -> dict[str, Any]:
        """
        Execute JavaScript code in all frames/iframes of the page.

        Args:
            code: JavaScript code to execute

        Returns:
            Results from all frames
        """
        try:
            # Get all frames
            frame_tree = await cdp_client.send_command("Page.getFrameTree")

            def extract_frames(frame_node: dict[str, Any]) -> list[dict[str, Any]]:
                frames = [frame_node["frame"]]
                for child in frame_node.get("childFrames", []):
                    frames.extend(extract_frames(child))
                return frames

            all_frames = extract_frames(frame_tree["frameTree"])

            results = []

            for frame in all_frames:
                frame_id = frame["id"]
                frame_url = frame.get("url", "about:blank")

                try:
                    # Execute code in this frame's context
                    result = await cdp_client.send_command(
                        "Runtime.evaluate",
                        {
                            "expression": code,
                            "returnByValue": True,
                            "contextId": None,  # Use default context for now
                        },
                    )

                    if result.get("exceptionDetails"):
                        frame_result = {
                            "frameId": frame_id,
                            "frameUrl": frame_url,
                            "success": False,
                            "error": result["exceptionDetails"].get("text", "Unknown error"),
                        }
                    else:
                        frame_result = {
                            "frameId": frame_id,
                            "frameUrl": frame_url,
                            "success": True,
                            "result": result.get("result", {}),
                            "value": result.get("result", {}).get("value"),
                        }

                    results.append(frame_result)

                except Exception as frame_error:
                    results.append(
                        {
                            "frameId": frame_id,
                            "frameUrl": frame_url,
                            "success": False,
                            "error": str(frame_error),
                        }
                    )

            return create_success_response(data={"framesCount": len(results), "results": results})

        except Exception as e:
            return create_error_response(f"Error evaluating in frames: {e}")
