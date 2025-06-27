#!/usr/bin/env python3
"""CSS Style Analysis Tools

This module provides CSS inspection and analysis capabilities through the
DevTools Protocol. It enables examination of computed styles, CSS rule matching,
stylesheet analysis, and CSS coverage tracking for web development and debugging.

The tools support CSS workflow analysis including cascade resolution, inheritance
tracking, pseudo-element inspection, and performance optimisation through coverage analysis.
All operations integrate with Chrome's CSS domain for accurate real-time style information.

Key Features:
    - Computed style calculation and property analysis
    - CSS rule matching and cascade inspection
    - Stylesheet content retrieval and analysis
    - Font and colour information extraction
    - Media query enumeration and analysis
    - CSS class name collection from stylesheets
    - CSS coverage tracking for performance optimisation
    - Background colour and typography analysis

Example:
    Analysing element styles and CSS coverage:

    ```python
    # Get computed styles for an element
    styles = await get_computed_styles(node_id=123)

    # Analyse CSS rule matching
    rules = await get_matched_styles(node_id=123)

    # Track CSS coverage for optimisation
    await start_css_coverage_tracking()
    # ... user interactions ...
    coverage = await stop_css_coverage_tracking()
    ```

Note:
    All CSS operations require an active connection to Chrome with the CSS domain enabled.
    The module automatically handles complex CSS data structures and provides sanitised
    responses suitable for analysis and debugging.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ..cdp_context import require_cdp_client
from .utils import create_error_response, create_success_response


def register_css_tools(mcp: FastMCP) -> None:
    """Register comprehensive CSS analysis tools with the MCP server.

    Adds all CSS inspection and analysis functions as MCP tools, providing complete
    stylesheet analysis, style computation, and CSS debugging capabilities. Each tool
    includes robust error handling and detailed response formatting.

    The registered tools support the full CSS development workflow:
    - Style computation and property analysis
    - CSS rule matching and cascade inspection
    - Stylesheet content analysis and class collection
    - Font and colour information extraction
    - Media query analysis and responsive design inspection
    - CSS coverage tracking for performance optimisation

    Args:
        mcp: FastMCP server instance to register tools with. Must be properly
             initialised before calling this function.

    Registered Tools:
        - get_computed_styles: Complete computed CSS properties
        - get_inline_styles: Inline and attribute-based styles
        - get_matched_styles: Comprehensive rule matching analysis
        - get_stylesheet_text: Stylesheet content retrieval
        - get_background_colors: Background and font information
        - get_platform_fonts: Font usage analysis
        - get_media_queries: Media query enumeration
        - collect_css_class_names: Class name collection
        - start_css_coverage_tracking: Coverage analysis initiation
        - stop_css_coverage_tracking: Coverage results and analysis

    Note:
        All tools require access to the global CDP client instance and active
        browser connection with CSS domain enabled. Tools will return appropriate
        error responses if the client is unavailable or disconnected.
    """

    @mcp.tool()
    @require_cdp_client
    async def get_computed_styles(cdp_client: Any, node_id: int) -> dict[str, Any]:
        """Retrieve computed CSS styles for a DOM element.

        Calculates and returns all computed CSS properties for the specified DOM element.
        This includes styles from all sources (stylesheets, inline styles, user agent styles)
        after CSS cascade resolution, inheritance, and computation of values.

        The computed styles represent the final values that the browser uses for rendering,
        taking into account all CSS rules, inheritance, and default values.

        Args:
            node_id: DOM node ID of the target element. Must be a valid node ID
                     obtained from DOM inspection tools.

        Returns:
            Computed styles dictionary containing:
            - success: Boolean indicating operation success
            - message: Summary of computed properties retrieved
            - data: Style information including:
                - nodeId: The target element's node ID
                - styles: Dictionary of CSS property names to computed values
                - totalProperties: Count of computed CSS properties

        Note:
            Computed values may differ from authored values due to CSS processing,
            inheritance, and browser-specific calculations.
        """
        try:
            result = await cdp_client.send_command(
                "CSS.getComputedStyleForNode", {"nodeId": node_id}
            )

            styles = {}
            for prop in result["computedStyle"]:
                styles[prop["name"]] = prop["value"]

            return create_success_response(
                message=f"Retrieved {len(styles)} computed CSS properties for node {node_id}",
                data={"nodeId": node_id, "styles": styles, "totalProperties": len(styles)},
            )

        except Exception as e:
            return create_error_response(f"Error getting computed styles: {e}")

    @mcp.tool()
    @require_cdp_client
    async def get_inline_styles(cdp_client: Any, node_id: int) -> dict[str, Any]:
        """
        Get inline CSS styles for a DOM element.

        Args:
            node_id: Node ID of the element

        Returns:
            Inline styles and attribute-based styles
        """
        try:
            result = await cdp_client.send_command(
                "CSS.getInlineStylesForNode", {"nodeId": node_id}
            )

            inline_styles = {}
            attribute_styles = {}

            if result.get("inlineStyle") and result["inlineStyle"].get("cssProperties"):
                for prop in result["inlineStyle"]["cssProperties"]:
                    inline_styles[prop["name"]] = prop["value"]

            if result.get("attributesStyle") and result["attributesStyle"].get("cssProperties"):
                for prop in result["attributesStyle"]["cssProperties"]:
                    attribute_styles[prop["name"]] = prop["value"]

            return create_success_response(
                message=f"Retrieved inline styles for node {node_id}",
                data={
                    "nodeId": node_id,
                    "inlineStyles": inline_styles,
                    "attributeStyles": attribute_styles,
                    "hasInlineStyles": len(inline_styles) > 0,
                    "hasAttributeStyles": len(attribute_styles) > 0,
                },
            )

        except Exception as e:
            return create_error_response(f"Error getting inline styles: {e}")

    @mcp.tool()
    @require_cdp_client
    async def get_matched_styles(cdp_client: Any, node_id: int) -> dict[str, Any]:
        """
        Get comprehensive style information including all CSS rules matching a DOM element.

        Args:
            node_id: Node ID of the element

        Returns:
            Complete style analysis including cascade, inheritance, and pseudo-elements
        """
        try:
            result = await cdp_client.send_command(
                "CSS.getMatchedStylesForNode", {"nodeId": node_id}
            )

            matched_rules = []
            if result.get("matchedCSSRules"):
                for rule in result["matchedCSSRules"]:
                    rule_info = {
                        "selector": rule["rule"]["selectorList"]["text"],
                        "origin": rule.get("origin", "unknown"),
                        "properties": {},
                    }

                    if rule["rule"].get("style") and rule["rule"]["style"].get("cssProperties"):
                        for prop in rule["rule"]["style"]["cssProperties"]:
                            rule_info["properties"][prop["name"]] = prop["value"]

                    matched_rules.append(rule_info)

            pseudo_elements = []
            if result.get("pseudoElements"):
                for pseudo in result["pseudoElements"]:
                    pseudo_info = {"pseudoType": pseudo["pseudoType"], "properties": {}}

                    if pseudo.get("matchedCSSRules"):
                        for rule in pseudo["matchedCSSRules"]:
                            if rule["rule"].get("style") and rule["rule"]["style"].get(
                                "cssProperties"
                            ):
                                for prop in rule["rule"]["style"]["cssProperties"]:
                                    pseudo_info["properties"][prop["name"]] = prop["value"]

                    pseudo_elements.append(pseudo_info)

            inherited = []
            if result.get("inherited"):
                for inherit in result["inherited"]:
                    inherit_info: dict[str, Any] = {"properties": {}, "matchedRules": []}

                    if inherit.get("inlineStyle") and inherit["inlineStyle"].get("cssProperties"):
                        for prop in inherit["inlineStyle"]["cssProperties"]:
                            inherit_info["properties"][prop["name"]] = prop["value"]

                    if inherit.get("matchedCSSRules"):
                        for rule in inherit["matchedCSSRules"]:
                            inherit_info["matchedRules"].append(
                                {
                                    "selector": rule["rule"]["selectorList"]["text"],
                                    "origin": rule.get("origin", "unknown"),
                                }
                            )

                    inherited.append(inherit_info)

            return create_success_response(
                message=f"Retrieved comprehensive style analysis for node {node_id}",
                data={
                    "nodeId": node_id,
                    "matchedRules": matched_rules,
                    "pseudoElements": pseudo_elements,
                    "inherited": inherited,
                    "matchedRulesCount": len(matched_rules),
                    "pseudoElementsCount": len(pseudo_elements),
                    "inheritedCount": len(inherited),
                },
            )

        except Exception as e:
            return create_error_response(f"Error getting matched styles: {e}")

    @mcp.tool()
    @require_cdp_client
    async def get_stylesheet_text(
        cdp_client: Any, stylesheet_id: str
    ) -> dict[str, Any]:
        """
        Get the textual content of a CSS stylesheet.

        Args:
            stylesheet_id: ID of the stylesheet

        Returns:
            Full text content of the stylesheet
        """
        try:
            result = await cdp_client.send_command(
                "CSS.getStyleSheetText", {"styleSheetId": stylesheet_id}
            )

            text = result["text"]
            return create_success_response(
                message=f"Retrieved stylesheet content (ID: {stylesheet_id})",
                data={
                    "styleSheetId": stylesheet_id,
                    "text": text,
                    "characterCount": len(text),
                    "lineCount": text.count("\n") + 1 if text else 0,
                },
            )

        except Exception as e:
            return create_error_response(f"Error getting stylesheet text: {e}")

    @mcp.tool()
    @require_cdp_client
    async def get_background_colors(
        cdp_client: Any, node_id: int
    ) -> dict[str, Any]:
        """
        Get background colors and font information for a DOM element.

        Args:
            node_id: Node ID of the element

        Returns:
            Background colors, computed font size, and font weight
        """
        try:
            result = await cdp_client.send_command("CSS.getBackgroundColors", {"nodeId": node_id})

            return create_success_response(
                message=f"Retrieved background color information for node {node_id}",
                data={
                    "nodeId": node_id,
                    "backgroundColors": result.get("backgroundColors", []),
                    "computedFontSize": result.get("computedFontSize"),
                    "computedFontWeight": result.get("computedFontWeight"),
                    "hasBackgroundColors": len(result.get("backgroundColors", [])) > 0,
                },
            )

        except Exception as e:
            return create_error_response(f"Error getting background colors: {e}")

    @mcp.tool()
    @require_cdp_client
    async def get_platform_fonts(cdp_client: Any, node_id: int) -> dict[str, Any]:
        """
        Get platform font usage information for a DOM element.

        Args:
            node_id: Node ID of the element

        Returns:
            Information about platform fonts used to render text nodes
        """
        try:
            result = await cdp_client.send_command(
                "CSS.getPlatformFontsForNode", {"nodeId": node_id}
            )

            fonts = result.get("fonts", [])
            font_info = []

            for font in fonts:
                font_info.append(
                    {
                        "familyName": font.get("familyName"),
                        "isCustomFont": font.get("isCustomFont", False),
                        "glyphCount": font.get("glyphCount", 0),
                    }
                )

            return create_success_response(
                message=f"Retrieved platform font information for node {node_id}",
                data={
                    "nodeId": node_id,
                    "fonts": font_info,
                    "fontCount": len(font_info),
                    "customFonts": [f for f in font_info if f["isCustomFont"]],
                    "systemFonts": [f for f in font_info if not f["isCustomFont"]],
                },
            )

        except Exception as e:
            return create_error_response(f"Error getting platform fonts: {e}")

    @mcp.tool()
    @require_cdp_client
    async def get_media_queries(cdp_client: Any) -> dict[str, Any]:
        """
        Get all media queries parsed by the rendering engine.

        Returns:
            List of all active media queries
        """
        try:
            result = await cdp_client.send_command("CSS.getMediaQueries")

            medias = result.get("medias", [])
            media_info = []

            for media in medias:
                media_info.append(
                    {
                        "text": media.get("text"),
                        "source": media.get("source"),
                        "sourceURL": media.get("sourceURL"),
                        "range": media.get("range"),
                        "styleSheetId": media.get("styleSheetId"),
                        "mediaList": media.get("mediaList", []),
                    }
                )

            return create_success_response(
                message=f"Retrieved {len(media_info)} media queries",
                data={
                    "mediaQueries": media_info,
                    "totalCount": len(media_info),
                    "sources": list({m["source"] for m in media_info if m.get("source")}),
                },
            )

        except Exception as e:
            return create_error_response(f"Error getting media queries: {e}")

    @mcp.tool()
    @require_cdp_client
    async def collect_css_class_names(
        cdp_client: Any, stylesheet_id: str
    ) -> dict[str, Any]:
        """
        Collect all class names from a specified stylesheet.

        Args:
            stylesheet_id: ID of the stylesheet to analyse

        Returns:
            List of all CSS class names found in the stylesheet
        """
        try:
            result = await cdp_client.send_command(
                "CSS.collectClassNames", {"styleSheetId": stylesheet_id}
            )

            class_names = result.get("classNames", [])

            return create_success_response(
                message=f"Collected {len(class_names)} class names from stylesheet {stylesheet_id}",
                data={
                    "styleSheetId": stylesheet_id,
                    "classNames": sorted(class_names),
                    "totalCount": len(class_names),
                },
            )

        except Exception as e:
            return create_error_response(f"Error collecting class names: {e}")

    @mcp.tool()
    @require_cdp_client
    async def start_css_coverage_tracking(cdp_client: Any) -> dict[str, Any]:
        """
        Start tracking CSS rule usage for coverage analysis.

        Returns:
            Status of coverage tracking initialization
        """
        try:
            await cdp_client.send_command("CSS.startRuleUsageTracking")

            return create_success_response(
                message="Started CSS coverage tracking", data={"tracking": True, "status": "active"}
            )

        except Exception as e:
            return create_error_response(f"Error starting CSS coverage tracking: {e}")

    @mcp.tool()
    @require_cdp_client
    async def stop_css_coverage_tracking(cdp_client: Any) -> dict[str, Any]:
        """
        Stop tracking CSS rule usage and get coverage results.

        Returns:
            CSS usage analysis with covered and uncovered rules
        """
        try:
            result = await cdp_client.send_command("CSS.stopRuleUsageTracking")

            rule_usage = result.get("ruleUsage", [])
            used_rules = [rule for rule in rule_usage if rule.get("used", False)]
            unused_rules = [rule for rule in rule_usage if not rule.get("used", False)]

            return create_success_response(
                message=f"Stopped CSS coverage tracking - analysed {len(rule_usage)} rules",
                data={
                    "tracking": False,
                    "totalRules": len(rule_usage),
                    "usedRules": len(used_rules),
                    "unusedRules": len(unused_rules),
                    "coveragePercentage": (len(used_rules) / len(rule_usage) * 100)
                    if rule_usage
                    else 0,
                    "ruleUsage": rule_usage,
                },
            )

        except Exception as e:
            return create_error_response(f"Error stopping CSS coverage tracking: {e}")
