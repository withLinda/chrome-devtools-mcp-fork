"""Chrome DevTools MCP Fork - Clean Architecture Version 2.0"""

__version__ = "2.0.0"

# Import main entry point for programmatic access
from chrome_devtools_mcp_fork.main import main, app

__all__ = ["main", "app", "__version__"]