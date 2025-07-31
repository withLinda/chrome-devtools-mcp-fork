#!/usr/bin/env python3
"""
Chrome DevTools MCP Server - Core Implementation

A comprehensive Model Context Protocol server that provides Chrome DevTools Protocol
integration for debugging web applications during development.

This module initialises all tool registrations and manages the global CDP client instance.
The Chrome DevTools Protocol client is implemented in a separate module to avoid
circular import issues.

The server provides tools for:
- Browser automation and management
- Network request monitoring and analysis
- DOM inspection and manipulation
- Console log retrieval and filtering
- Performance metrics collection
- CSS computed styles analysis
- Local storage and session storage management

All tools follow defensive programming principles with comprehensive error handling,
input validation, and clear error messages for robust operation.
"""

from __future__ import annotations

import logging

from mcp.server.fastmcp import FastMCP

from client import ChromeDevToolsClient
from tools import (
    register_chrome_tools,
    register_console_tools,
    register_css_tools,
    register_dom_tools,
    register_network_tools,
    register_performance_tools,
    register_storage_tools,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialise the MCP server with a descriptive name
mcp = FastMCP("Chrome DevTools MCP")
mcp.dependencies = ["websockets>=12.0", "aiohttp>=3.9.0"]

# Export public interface for external access
__all__ = ["mcp", "main", "ChromeDevToolsClient"]

# Global CDP client instance - initialised when first tool is called
cdp_client: ChromeDevToolsClient | None = None


def register_all_tools() -> None:
    """Register all MCP tools with the server."""
    logger.info("Registering MCP tools...")

    register_chrome_tools(mcp)
    register_network_tools(mcp)
    register_console_tools(mcp)
    register_dom_tools(mcp)
    register_css_tools(mcp)
    register_storage_tools(mcp)
    register_performance_tools(mcp)

    logger.info("All MCP tools registered successfully")


# Initialise CDP client and register tools when module is imported
cdp_client = ChromeDevToolsClient()
register_all_tools()


def main() -> None:
    """Main server entry point."""
    logger.info("Starting Chrome DevTools MCP...")
    mcp.run()


if __name__ == "__main__":
    main()
