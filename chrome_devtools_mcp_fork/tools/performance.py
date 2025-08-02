"""Performance tools for Chrome DevTools MCP"""

from chrome_devtools_mcp_fork.utils.helpers import create_success_response

def register_tools(app):
    """Register performance tools with FastMCP app."""
    
    @app.tool()
    def get_performance_metrics() -> dict:
        """Get performance metrics (placeholder implementation)."""
        return create_success_response({}, "Performance metrics retrieved")