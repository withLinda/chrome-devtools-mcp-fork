#!/usr/bin/env python3
"""
Chrome DevTools MCP Fork - Main Entry Point

This file is designed to work in multiple execution contexts:
1. Direct execution: python main.py
2. Module execution: python -m chrome_devtools_mcp_fork
3. Package import: from chrome_devtools_mcp_fork import main
"""

import logging
import sys
from pathlib import Path

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_import_paths():
    """
    Setup import paths to handle both script and module execution.
    This is the KEY fix for the relative import issues.
    """
    # Get the directory containing this file
    current_dir = Path(__file__).parent.absolute()

    # Add current directory to Python path if not already there
    current_dir_str = str(current_dir)
    if current_dir_str not in sys.path:
        sys.path.insert(0, current_dir_str)
        logger.debug(f"Added {current_dir_str} to sys.path")

    # If we're being executed as __main__, we need special handling
    if __name__ == "__main__":
        # Add parent directory for package imports
        parent_dir = current_dir.parent
        parent_dir_str = str(parent_dir)
        if parent_dir_str not in sys.path:
            sys.path.insert(0, parent_dir_str)
            logger.debug(f"Added {parent_dir_str} to sys.path for __main__ execution")

# Setup paths BEFORE any imports
setup_import_paths()

# Now try imports with fallback strategies
def safe_import():
    """Import required modules with multiple fallback strategies."""

    # Strategy 1: Try relative imports (works when imported as module)
    try:
        from mcp.server.fastmcp import FastMCP

        from .client import ChromeDevToolsClient
        from .tools import (
            register_chrome_tools,
            register_console_tools,
            register_css_tools,
            register_dom_tools,
            register_network_tools,
            register_performance_tools,
            register_storage_tools,
        )
        logger.info("✅ Successfully imported using relative imports")
        return ChromeDevToolsClient, (register_chrome_tools, register_console_tools,
                                      register_css_tools, register_dom_tools,
                                      register_network_tools, register_performance_tools,
                                      register_storage_tools), FastMCP
    except ImportError as e:
        logger.debug(f"Relative import failed: {e}")

    # Strategy 2: Try absolute imports (works when package is properly installed)
    try:
        from mcp.server.fastmcp import FastMCP

        from chrome_devtools_mcp_fork.client import ChromeDevToolsClient
        from chrome_devtools_mcp_fork.tools import (
            register_chrome_tools,
            register_console_tools,
            register_css_tools,
            register_dom_tools,
            register_network_tools,
            register_performance_tools,
            register_storage_tools,
        )
        logger.info("✅ Successfully imported using absolute imports")
        return ChromeDevToolsClient, (register_chrome_tools, register_console_tools,
                                      register_css_tools, register_dom_tools,
                                      register_network_tools, register_performance_tools,
                                      register_storage_tools), FastMCP
    except ImportError as e:
        logger.debug(f"Absolute import failed: {e}")

    # Strategy 3: Try direct imports (works when executed as script)
    try:
        from mcp.server.fastmcp import FastMCP

        import client
        import tools.chrome_management
        import tools.console
        import tools.css
        import tools.dom
        import tools.network
        import tools.performance
        import tools.storage

        logger.info("✅ Successfully imported using direct imports")
        return client.ChromeDevToolsClient, (tools.chrome_management.register_chrome_tools,
                                            tools.console.register_console_tools,
                                            tools.css.register_css_tools,
                                            tools.dom.register_dom_tools,
                                            tools.network.register_network_tools,
                                            tools.performance.register_performance_tools,
                                            tools.storage.register_storage_tools), FastMCP

    except ImportError as e:
        logger.error(f"❌ All import strategies failed: {e}")
        raise ImportError(
            "Could not import required modules. "
            "Please ensure chrome-devtools-mcp-fork is properly installed."
        ) from e

# Import with fallback
try:
    ChromeDevToolsClient, tool_registrations, FastMCP = safe_import()
except ImportError:
    logger.error("Failed to import required components")
    sys.exit(1)

# Global instances - initialized lazily
cdp_client = None
mcp = None

def get_mcp_server():
    """Get or create the MCP server instance."""
    global mcp
    if mcp is None:
        mcp = FastMCP("Chrome DevTools MCP")
    return mcp

def register_all_tools():
    """Register all MCP tools with the server."""
    server = get_mcp_server()
    (register_chrome_tools, register_console_tools, register_css_tools,
     register_dom_tools, register_network_tools, register_performance_tools,
     register_storage_tools) = tool_registrations

    register_chrome_tools(server)
    register_console_tools(server)
    register_css_tools(server)
    register_dom_tools(server)
    register_network_tools(server)
    register_performance_tools(server)
    register_storage_tools(server)

def main():
    """Main entry point for the MCP server."""
    logger.info("🚀 Starting Chrome DevTools MCP Fork server...")

    try:
        # Initialize CDP client
        global cdp_client
        cdp_client = ChromeDevToolsClient()

        # Register all MCP tools
        logger.info("📝 Registering MCP tools...")
        register_all_tools()
        logger.info("✅ All MCP tools registered successfully")

        # Start the MCP server
        logger.info("🔌 Starting MCP server...")
        server = get_mcp_server()
        server.run()

    except Exception as e:
        logger.error(f"❌ Failed to start MCP server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
