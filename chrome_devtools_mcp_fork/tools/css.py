"""CSS tools for Chrome DevTools MCP"""

from chrome_devtools_mcp_fork.utils.helpers import create_success_response

def register_tools(app):
    """Register CSS tools with FastMCP app."""
    
    @app.tool()
    def get_computed_styles(node_id: int) -> dict:
        """Get computed styles (placeholder implementation)."""
        return create_success_response({}, "Computed styles retrieved")