"""Network tools for Chrome DevTools MCP"""

from chrome_devtools_mcp_fork.utils.helpers import create_success_response


def register_tools(app):
    """Register network tools with FastMCP app."""

    @app.tool()
    def get_network_requests() -> dict:
        """Get network requests (placeholder implementation)."""
        return create_success_response([], "Network requests retrieved")
