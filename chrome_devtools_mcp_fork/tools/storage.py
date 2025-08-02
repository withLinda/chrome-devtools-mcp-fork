"""Storage tools for Chrome DevTools MCP"""

from chrome_devtools_mcp_fork.utils.helpers import create_success_response


def register_tools(app):
    """Register storage tools with FastMCP app."""

    @app.tool()
    def get_all_cookies() -> dict:
        """Get all cookies (placeholder implementation)."""
        return create_success_response([], "Cookies retrieved")
