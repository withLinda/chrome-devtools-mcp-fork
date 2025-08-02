#!/usr/bin/env python3
"""
Chrome DevTools MCP Fork - FastMCP Implementation
Clean architecture with absolute imports only.
"""

import sys
import logging

# Import MCP SDK
from mcp.server.fastmcp import FastMCP

# Import our tools with absolute imports only
from chrome_devtools_mcp_fork.tools import browser
from chrome_devtools_mcp_fork.tools import console
from chrome_devtools_mcp_fork.tools import css
from chrome_devtools_mcp_fork.tools import dom
from chrome_devtools_mcp_fork.tools import network
from chrome_devtools_mcp_fork.tools import performance
from chrome_devtools_mcp_fork.tools import storage

# Configure logging for MCP (never write to stdout for STDIO servers)
logging.basicConfig(
    level=logging.WARNING,  # Only warnings and errors
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]  # Use stderr, never stdout
)
logger = logging.getLogger(__name__)

# Create FastMCP app instance
app = FastMCP("chrome-devtools-mcp-fork")

# Register all tools
browser.register_tools(app)
console.register_tools(app)
css.register_tools(app)
dom.register_tools(app)
network.register_tools(app)
performance.register_tools(app)
storage.register_tools(app)

def main():
    """Main entry point for the MCP server."""
    try:
        logger.warning("Starting Chrome DevTools MCP Fork server v2.0.0")
        app.run()
    except Exception as e:
        logger.error(f"Failed to start MCP server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()