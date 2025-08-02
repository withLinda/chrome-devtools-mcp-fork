"""DOM tools for Chrome DevTools MCP"""

from chrome_devtools_mcp_fork.utils.helpers import create_success_response

def register_tools(app):
    """Register DOM tools with FastMCP app."""
    
    @app.tool()
    def get_document(depth: int = 1) -> dict:
        """Get DOM document (placeholder implementation)."""
        return create_success_response({}, "Document retrieved")