"""Console tools for Chrome DevTools MCP"""

from chrome_devtools_mcp_fork.utils.helpers import create_success_response, create_error_response

def register_tools(app):
    """Register console tools with FastMCP app."""
    
    @app.tool()
    def get_console_logs() -> dict:
        """Get console logs (placeholder implementation)."""
        return create_success_response([], "Console logs retrieved")
    
    @app.tool()
    def clear_console() -> dict:
        """Clear console (placeholder implementation)."""
        return create_success_response(None, "Console cleared")