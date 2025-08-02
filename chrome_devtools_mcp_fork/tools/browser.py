"""Browser management tools for Chrome DevTools MCP"""

import asyncio
import tempfile
import subprocess
import platform
from typing import Dict, Any, Optional

from chrome_devtools_mcp_fork.utils.helpers import create_success_response, create_error_response
from chrome_devtools_mcp_fork.client import ChromeDevToolsClient

# Global client instance
client = ChromeDevToolsClient()

def register_tools(app):
    """Register browser management tools with FastMCP app."""
    
    @app.tool()
    def start_chrome(port: int = 9222, headless: bool = False, chrome_path: Optional[str] = None) -> Dict[str, Any]:
        """Start Chrome with remote debugging enabled."""
        try:
            # Determine Chrome path based on platform
            if chrome_path is None:
                system = platform.system()
                if system == "Darwin":  # macOS
                    chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
                elif system == "Windows":
                    chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
                else:  # Linux
                    chrome_path = "google-chrome"
            
            # Create temporary user data directory
            user_data_dir = tempfile.mkdtemp(prefix="chrome-mcp-")
            
            # Build Chrome command
            cmd = [
                chrome_path,
                f"--remote-debugging-port={port}",
                f"--user-data-dir={user_data_dir}",
                "--no-first-run",
                "--no-default-browser-check"
            ]
            
            if headless:
                cmd.append("--headless")
            
            # Start Chrome process
            process = subprocess.Popen(cmd, 
                                     stdout=subprocess.DEVNULL, 
                                     stderr=subprocess.DEVNULL)
            
            # Wait a moment for Chrome to start
            import time
            time.sleep(2)
            
            return create_success_response({
                "pid": process.pid,
                "port": port,
                "headless": headless,
                "user_data_dir": user_data_dir
            }, "Chrome started successfully")
            
        except Exception as e:
            return create_error_response(f"Failed to start Chrome: {str(e)}")
    
    @app.tool()
    def connect_to_browser(port: int = 9222) -> Dict[str, Any]:
        """Connect to a running Chrome instance."""
        try:
            result = client.connect(port)
            if result:
                return create_success_response({
                    "connected": True,
                    "port": port
                }, "Connected to Chrome successfully")
            else:
                return create_error_response("Failed to connect to Chrome")
        except Exception as e:
            return create_error_response(f"Connection failed: {str(e)}")
    
    @app.tool()
    def get_connection_status() -> Dict[str, Any]:
        """Get current connection status."""
        try:
            if client.is_connected():
                return create_success_response({
                    "connected": True,
                    "status": "connected"
                }, "Browser is connected")
            else:
                return create_error_response("Not connected to browser. Please connect to Chrome first.")
        except Exception as e:
            return create_error_response(f"Status check failed: {str(e)}")
    
    @app.tool()
    def start_chrome_and_connect(url: str, port: int = 9222, headless: bool = False) -> Dict[str, Any]:
        """Start Chrome and connect in one operation."""
        try:
            # Start Chrome
            start_result = start_chrome(port=port, headless=headless)
            if not start_result["success"]:
                return start_result
            
            # Wait for Chrome to be ready
            import time
            time.sleep(3)
            
            # Connect to Chrome
            connect_result = connect_to_browser(port=port)
            if not connect_result["success"]:
                return connect_result
            
            # Navigate to URL
            nav_result = navigate_to_url(url)
            
            return create_success_response({
                "chrome": start_result["data"],
                "connection": connect_result["data"],
                "navigation": nav_result
            }, f"Chrome started and navigated to {url}")
            
        except Exception as e:
            return create_error_response(f"Start and connect failed: {str(e)}")
    
    @app.tool()
    def navigate_to_url(url: str) -> Dict[str, Any]:
        """Navigate to a specific URL."""
        try:
            if not client.is_connected():
                return create_error_response("Not connected to browser")
            
            result = client.navigate(url)
            if result:
                return create_success_response({
                    "url": url,
                    "navigated": True
                }, f"Navigated to {url}")
            else:
                return create_error_response("Navigation failed")
                
        except Exception as e:
            return create_error_response(f"Navigation error: {str(e)}")