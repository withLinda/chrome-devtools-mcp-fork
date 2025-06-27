#!/usr/bin/env python3
"""Chrome DevTools MCP Tools Package.

This package provides Chrome DevTools Protocol integration for the MCP server,
enabling automated browser control, inspection, and debugging through standardised tools.

The tools are organised into logical groups covering all major aspects of web development and
browser interaction:

- Chrome Management: Browser lifecycle control (start, connect, navigate)
- Console Operations: JavaScript execution and console monitoring
- DOM Inspection: Element querying, modification, and analysis
- CSS Analysis: Style computation, rule matching, and coverage tracking
- Network Monitoring: Request/response capture and analysis
- Performance Profiling: Metrics collection and resource timing
- Storage Management: Cookies, localStorage, and quota management

Each tool group is designed for integration with Chrome's debugging protocol,
providing error handling and response formatting.

Example:
    Basic usage pattern for tool registration:
    
    ```python
    from mcp.server.fastmcp import FastMCP
    from .chrome_management import register_chrome_tools
    
    mcp = FastMCP("devtools-server")
    register_chrome_tools(mcp)
    ```

Attributes:
    __all__: List of available tool registration functions for import control.
"""

from .chrome_management import register_chrome_tools
from .console import register_console_tools
from .css import register_css_tools
from .dom import register_dom_tools
from .network import register_network_tools
from .performance import register_performance_tools
from .storage import register_storage_tools

__all__ = [
    "register_chrome_tools",
    "register_network_tools",
    "register_console_tools",
    "register_dom_tools",
    "register_css_tools",
    "register_storage_tools",
    "register_performance_tools",
]
