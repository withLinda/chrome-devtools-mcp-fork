"""Shared utility functions for Chrome DevTools MCP Fork"""

import time
from typing import Dict, Any, Optional

def create_success_response(data: Any = None, message: str = "Success") -> Dict[str, Any]:
    """Create a standardized success response."""
    return {
        "success": True,
        "message": message,
        "data": data,
        "timestamp": time.time()
    }

def create_error_response(error: str, details: Optional[Dict] = None) -> Dict[str, Any]:
    """Create a standardized error response."""
    return {
        "success": False,
        "error": error,
        "details": details or {},
        "timestamp": time.time()
    }

def safe_timestamp_conversion(timestamp: Any) -> Optional[float]:
    """Safely convert various timestamp formats to float."""
    if timestamp is None:
        return None
    
    try:
        return float(timestamp)
    except (ValueError, TypeError):
        return None