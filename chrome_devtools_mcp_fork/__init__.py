"""Chrome DevTools MCP Fork Package."""

__version__ = "1.0.7"

# Import main components for easy access
from .client import ChromeDevToolsClient
from .main import main, cdp_client, get_mcp_server

# Import all tool registration functions
from .tools import (
    register_chrome_tools,
    register_console_tools,
    register_css_tools, 
    register_dom_tools,
    register_network_tools,
    register_performance_tools,
    register_storage_tools,
)

__all__ = [
    "ChromeDevToolsClient",
    "main",
    "get_mcp_server",
    "cdp_client",
    "register_chrome_tools", 
    "register_console_tools",
    "register_css_tools",
    "register_dom_tools", 
    "register_network_tools",
    "register_performance_tools",
    "register_storage_tools",
]
