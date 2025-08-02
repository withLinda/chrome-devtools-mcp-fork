"""Chrome DevTools MCP Tools Package."""

# Import all registration functions
from .chrome_management import register_chrome_tools
from .console import register_console_tools  
from .css import register_css_tools
from .dom import register_dom_tools
from .network import register_network_tools
from .performance import register_performance_tools
from .storage import register_storage_tools

__all__ = [
    "register_chrome_tools",
    "register_console_tools", 
    "register_css_tools",
    "register_dom_tools",
    "register_network_tools", 
    "register_performance_tools",
    "register_storage_tools",
]
