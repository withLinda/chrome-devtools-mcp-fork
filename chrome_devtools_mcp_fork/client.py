"""Chrome DevTools Protocol client with absolute imports only"""

import json
import requests
import websocket
from typing import Dict, Any, Optional

class ChromeDevToolsClient:
    """Chrome DevTools Protocol client."""
    
    def __init__(self):
        self.ws = None
        self.port = None
        self.connected = False
    
    def connect(self, port: int = 9222) -> bool:
        """Connect to Chrome DevTools."""
        try:
            self.port = port
            
            # Get available tabs
            response = requests.get(f"http://localhost:{port}/json/list")
            tabs = response.json()
            
            if not tabs:
                return False
            
            # Connect to first tab
            tab = tabs[0]
            ws_url = tab['webSocketDebuggerUrl']
            
            self.ws = websocket.create_connection(ws_url)
            self.connected = True
            
            # Enable required domains
            self._send_command("Runtime.enable", {})
            self._send_command("Page.enable", {})
            self._send_command("DOM.enable", {})
            
            return True
            
        except Exception:
            self.connected = False
            return False
    
    def is_connected(self) -> bool:
        """Check if connected to Chrome."""
        return self.connected and self.ws is not None
    
    def navigate(self, url: str) -> bool:
        """Navigate to URL."""
        try:
            if not self.is_connected():
                return False
            
            result = self._send_command("Page.navigate", {"url": url})
            return result is not None
            
        except Exception:
            return False
    
    def _send_command(self, method: str, params: Dict[str, Any]) -> Optional[Dict]:
        """Send command to Chrome DevTools."""
        try:
            if not self.is_connected():
                return None
            
            command = {
                "id": 1,
                "method": method,
                "params": params
            }
            
            self.ws.send(json.dumps(command))
            response = self.ws.recv()
            return json.loads(response)
            
        except Exception:
            return None