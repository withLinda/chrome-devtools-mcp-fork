"""Chrome DevTools MCP Fork - Clean Architecture Version 2.0"""

__version__ = "2.0.1"

# Import main entry point for programmatic access
from chrome_devtools_mcp_fork.main import main, app


def get_mcp_server():
    """Return the FastMCP app instance for server.py"""
    from chrome_devtools_mcp_fork.main import app

    return app


__all__ = ["main", "app", "__version__", "get_mcp_server"]
