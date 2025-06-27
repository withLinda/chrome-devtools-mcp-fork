#!/usr/bin/env python3
"""DOM Element Inspection Tools

This module provides DOM manipulation and inspection capabilities through
the DevTools Protocol. It enables element querying, property analysis, structural
inspection, and interaction with the document object model of web pages.

The tools support DOM workflow operations including element discovery,
attribute analysis, content extraction, layout inspection, and element interaction.
All operations integrate with Chrome's DOM domain for accurate real-time
document state access.

Key Features:
    - Document structure retrieval with configurable depth
    - CSS selector-based element querying (single and multiple)
    - Element attribute and property inspection
    - HTML content extraction (outer HTML)
    - Box model and layout information analysis
    - Position-based element discovery
    - Text-based element searching with flexible queries
    - Element focus management and interaction

Example:
    Inspecting and interacting with DOM elements:

    ```python
    # Get document structure
    document = await get_document(depth=2, pierce=True)

    # Find elements by CSS selector
    buttons = await query_selector_all(node_id=1, selector='button.primary')

    # Inspect element properties
    attrs = await get_element_attributes(node_id=123)

    # Get layout information
    box_model = await get_element_box_model(node_id=123)
    ```

Note:
    All DOM operations require an active connection to Chrome with the DOM domain enabled.
    Node IDs are specific to the current page session and become invalid after navigation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mcp.server.fastmcp import FastMCP

from ..cdp_context import require_cdp_client
from .utils import create_error_response, create_success_response

if TYPE_CHECKING:
    from ..main import ChromeDevToolsClient


def register_dom_tools(mcp: FastMCP) -> None:
    """Register comprehensive DOM inspection and manipulation tools with the MCP server.

    Adds all DOM analysis and interaction functions as MCP tools, providing complete
    document object model access, element querying, and structural analysis capabilities.
    Each tool includes robust error handling and detailed response formatting.

    The registered tools support the full DOM development workflow:
    - Document structure analysis and navigation
    - Element discovery through CSS selectors and text search
    - Attribute and property inspection
    - Content extraction and analysis
    - Layout and positioning information
    - Element interaction and focus management

    Args:
        mcp: FastMCP server instance to register tools with. Must be properly
             initialised before calling this function.

    Registered Tools:
        - get_document: Document structure retrieval with depth control
        - query_selector: Single element CSS selector querying
        - query_selector_all: Multiple element CSS selector querying
        - get_element_attributes: Element attribute enumeration
        - get_element_outer_html: HTML content extraction
        - get_element_box_model: Layout and positioning analysis
        - describe_element: Comprehensive element description
        - get_element_at_position: Position-based element discovery
        - search_elements: Text-based element searching
        - focus_element: Element focus management

    Note:
        All tools require access to the global CDP client instance and active
        browser connection with DOM domain enabled. Node IDs are session-specific
        and become invalid after page navigation.
    """

    @mcp.tool()
    @require_cdp_client
    async def get_document(
        cdp_client: ChromeDevToolsClient, depth: int = 1, pierce: bool = False
    ) -> dict[str, Any]:
        """Retrieve the DOM document structure with configurable depth and shadow DOM access.

        Fetches the document tree starting from the root element, with control over
        traversal depth and shadow DOM boundary crossing. This provides the foundation
        for all DOM inspection operations by establishing the document structure.

        The depth parameter controls how deep into the DOM tree to traverse, while
        the pierce option enables inspection of shadow DOM content that would normally
        be encapsulated.

        Args:
            depth: Maximum depth to retrieve from document root (default: 1).
                   Use -1 to retrieve the entire document tree. Higher depths
                   provide more complete structure but increase response size.
            pierce: Whether to traverse shadow DOM boundaries (default: False).
                   When True, includes shadow DOM content in the tree structure.

        Returns:
            Document structure dictionary containing:
            - success: Boolean indicating retrieval success
            - message: Summary of document structure retrieved
            - data: Complete DOM tree structure from the document root,
                   including all child elements up to the specified depth

        Note:
            Large documents with high depth settings may produce substantial responses.
            Consider using moderate depths for initial exploration, then targeting
            specific areas for detailed analysis.
        """
        try:
            result = await cdp_client.send_command(
                "DOM.getDocument", {"depth": depth, "pierce": pierce}
            )

            return create_success_response(
                message=f"Retrieved DOM document structure (depth: {depth})", data=result["root"]
            )

        except Exception as e:
            return create_error_response(f"Error getting document: {e}")

    @mcp.tool()
    @require_cdp_client
    async def query_selector(
        cdp_client: ChromeDevToolsClient, node_id: int, selector: str
    ) -> dict[str, Any]:
        """
        Execute querySelector on a DOM node.

        Args:
            node_id: Target node ID to query within
            selector: CSS selector string

        Returns:
            Node ID of the matching element
        """
        try:
            result = await cdp_client.send_command(
                "DOM.querySelector", {"nodeId": node_id, "selector": selector}
            )

            if result["nodeId"] == 0:
                return create_success_response(
                    message=f"No element found matching selector: {selector}",
                    data={"nodeId": None, "found": False},
                )

            return create_success_response(
                message=f"Found element matching selector: {selector}",
                data={"nodeId": result["nodeId"], "found": True},
            )

        except Exception as e:
            return create_error_response(f"Error executing querySelector: {e}")

    @mcp.tool()
    @require_cdp_client
    async def query_selector_all(
        cdp_client: ChromeDevToolsClient, node_id: int, selector: str
    ) -> dict[str, Any]:
        """
        Execute querySelectorAll on a DOM node.

        Args:
            node_id: Target node ID to query within
            selector: CSS selector string

        Returns:
            Array of node IDs matching the selector
        """
        try:
            result = await cdp_client.send_command(
                "DOM.querySelectorAll", {"nodeId": node_id, "selector": selector}
            )

            return create_success_response(
                message=f"Found {len(result['nodeIds'])} elements matching selector: {selector}",
                data={"nodeIds": result["nodeIds"], "count": len(result["nodeIds"])},
            )

        except Exception as e:
            return create_error_response(f"Error executing querySelectorAll: {e}")

    @mcp.tool()
    @require_cdp_client
    async def get_element_attributes(
        cdp_client: ChromeDevToolsClient, node_id: int
    ) -> dict[str, Any]:
        """
        Get all attributes of a DOM element.

        Args:
            node_id: Node ID of the element

        Returns:
            Dictionary of element attributes
        """
        try:
            result = await cdp_client.send_command("DOM.getAttributes", {"nodeId": node_id})

            attributes = {}
            attr_list = result["attributes"]
            for i in range(0, len(attr_list), 2):
                if i + 1 < len(attr_list):
                    attributes[attr_list[i]] = attr_list[i + 1]

            return create_success_response(
                message=f"Retrieved {len(attributes)} attributes for node {node_id}",
                data={"nodeId": node_id, "attributes": attributes},
            )

        except Exception as e:
            return create_error_response(f"Error getting element attributes: {e}")

    @mcp.tool()
    @require_cdp_client
    async def get_element_outer_html(
        cdp_client: ChromeDevToolsClient, node_id: int
    ) -> dict[str, Any]:
        """
        Get the outer HTML of a DOM element.

        Args:
            node_id: Node ID of the element

        Returns:
            Outer HTML string of the element
        """
        try:
            result = await cdp_client.send_command("DOM.getOuterHTML", {"nodeId": node_id})

            return create_success_response(
                message=f"Retrieved outer HTML for node {node_id}",
                data={
                    "nodeId": node_id,
                    "outerHTML": result["outerHTML"],
                    "htmlLength": len(result["outerHTML"]),
                },
            )

        except Exception as e:
            return create_error_response(f"Error getting outer HTML: {e}")

    @mcp.tool()
    @require_cdp_client
    async def get_element_box_model(
        cdp_client: ChromeDevToolsClient, node_id: int
    ) -> dict[str, Any]:
        """
        Get the box model (layout information) of a DOM element.

        Args:
            node_id: Node ID of the element

        Returns:
            Box model data including content, padding, border, and margin boxes
        """
        try:
            result = await cdp_client.send_command("DOM.getBoxModel", {"nodeId": node_id})

            model = result["model"]
            return create_success_response(
                message=f"Retrieved box model for node {node_id}",
                data={
                    "nodeId": node_id,
                    "content": model["content"],
                    "padding": model["padding"],
                    "border": model["border"],
                    "margin": model["margin"],
                    "width": model["width"],
                    "height": model["height"],
                },
            )

        except Exception as e:
            return create_error_response(f"Error getting box model: {e}")

    @mcp.tool()
    @require_cdp_client
    async def describe_element(
        cdp_client: ChromeDevToolsClient, node_id: int, depth: int = 1
    ) -> dict[str, Any]:
        """
        Get detailed information about a DOM element.

        Args:
            node_id: Node ID of the element
            depth: Depth of child nodes to include

        Returns:
            Detailed element description including tag, attributes, and children
        """
        try:
            result = await cdp_client.send_command(
                "DOM.describeNode", {"nodeId": node_id, "depth": depth}
            )

            node = result["node"]
            return create_success_response(
                message=f"Retrieved description for node {node_id}",
                data={
                    "nodeId": node_id,
                    "nodeName": node.get("nodeName"),
                    "nodeType": node.get("nodeType"),
                    "nodeValue": node.get("nodeValue"),
                    "localName": node.get("localName"),
                    "attributes": node.get("attributes", []),
                    "childNodeCount": node.get("childNodeCount", 0),
                    "children": node.get("children", []),
                },
            )

        except Exception as e:
            return create_error_response(f"Error describing element: {e}")

    @mcp.tool()
    @require_cdp_client
    async def get_element_at_position(
        cdp_client: ChromeDevToolsClient, x: int, y: int
    ) -> dict[str, Any]:
        """
        Get the DOM element at a specific screen position.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            Node information at the specified position
        """
        try:
            result = await cdp_client.send_command("DOM.getNodeForLocation", {"x": x, "y": y})

            return create_success_response(
                message=f"Found element at position ({x}, {y})",
                data={
                    "position": {"x": x, "y": y},
                    "nodeId": result.get("nodeId"),
                    "backendNodeId": result.get("backendNodeId"),
                    "frameId": result.get("frameId"),
                },
            )

        except Exception as e:
            return create_error_response(f"Error getting element at position: {e}")

    @mcp.tool()
    @require_cdp_client
    async def search_elements(cdp_client: ChromeDevToolsClient, query: str) -> dict[str, Any]:
        """
        Search for DOM elements matching a query string.

        Args:
            query: Search query (text content, tag name, or attribute)

        Returns:
            Search results with matching elements
        """
        try:
            search_result = await cdp_client.send_command(
                "DOM.performSearch", {"query": query, "includeUserAgentShadowDOM": False}
            )

            search_id = search_result["searchId"]
            result_count = search_result["resultCount"]

            if result_count == 0:
                await cdp_client.send_command("DOM.discardSearchResults", {"searchId": search_id})
                return create_success_response(
                    message=f"No elements found matching query: {query}",
                    data={"query": query, "resultCount": 0, "nodeIds": []},
                )

            limit = min(result_count, 50)
            results = await cdp_client.send_command(
                "DOM.getSearchResults", {"searchId": search_id, "fromIndex": 0, "toIndex": limit}
            )

            await cdp_client.send_command("DOM.discardSearchResults", {"searchId": search_id})

            return create_success_response(
                message=f"Found {result_count} elements matching query: {query}",
                data={
                    "query": query,
                    "resultCount": result_count,
                    "nodeIds": results["nodeIds"],
                    "limitedResults": limit < result_count,
                },
            )

        except Exception as e:
            return create_error_response(f"Error searching elements: {e}")

    @mcp.tool()
    @require_cdp_client
    async def focus_element(cdp_client: ChromeDevToolsClient, node_id: int) -> dict[str, Any]:
        """
        Focus a DOM element.

        Args:
            node_id: Node ID of the element to focus

        Returns:
            Success status of the focus operation
        """
        try:
            await cdp_client.send_command("DOM.focus", {"nodeId": node_id})

            return create_success_response(
                message=f"Focused element with node ID {node_id}",
                data={"nodeId": node_id, "focused": True},
            )

        except Exception as e:
            return create_error_response(f"Error focusing element: {e}")
