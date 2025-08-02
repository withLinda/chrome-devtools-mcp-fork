"""Test core import and export functionality."""

import pytest
import sys
import subprocess
import os


def test_server_entry_point_imports():
    """Test server.py can import required functions."""
    try:
        from chrome_devtools_mcp_fork import get_mcp_server, main
        assert callable(get_mcp_server), "get_mcp_server should be callable"
        assert callable(main), "main should be callable"
    except ImportError as e:
        pytest.fail(f"Failed to import from chrome_devtools_mcp_fork: {e}")


def test_package_exports():
    """Verify all required exports in __init__.py."""
    import chrome_devtools_mcp_fork
    
    # Check all expected exports
    expected_exports = ['get_mcp_server', 'main', 'app', '__version__']
    for export in expected_exports:
        assert hasattr(chrome_devtools_mcp_fork, export), f"Missing export: {export}"
    
    # Verify __all__ list
    assert '__all__' in dir(chrome_devtools_mcp_fork)
    assert set(chrome_devtools_mcp_fork.__all__) == set(expected_exports)


def test_get_mcp_server_returns_app():
    """Test get_mcp_server returns the FastMCP app instance."""
    from chrome_devtools_mcp_fork import get_mcp_server, app
    
    server = get_mcp_server()
    assert server is app, "get_mcp_server should return the same app instance"


def test_no_relative_imports():
    """Ensure no relative imports exist in the codebase."""
    # Get the package directory
    import chrome_devtools_mcp_fork
    package_dir = os.path.dirname(chrome_devtools_mcp_fork.__file__)
    
    # Check all Python files for relative imports
    relative_import_patterns = ["from .", "from .."]
    found_relative_imports = []
    
    for root, dirs, files in os.walk(package_dir):
        # Skip __pycache__ directories
        dirs[:] = [d for d in dirs if d != '__pycache__']
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r') as f:
                    content = f.read()
                    for line_num, line in enumerate(content.splitlines(), 1):
                        for pattern in relative_import_patterns:
                            if pattern in line and not line.strip().startswith('#'):
                                found_relative_imports.append(
                                    f"{filepath}:{line_num}: {line.strip()}"
                                )
    
    assert not found_relative_imports, (
        "Found relative imports:\n" + "\n".join(found_relative_imports)
    )


def test_server_py_import_in_subprocess():
    """Test that server.py can be imported in a subprocess (simulates MCP execution)."""
    # Get the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Python code to test imports
    test_code = """
import sys
sys.path.insert(0, r'{}')

# Test import
from chrome_devtools_mcp_fork import get_mcp_server, main
mcp = get_mcp_server()
print("SUCCESS: All imports worked")
""".format(project_root)
    
    # Run in subprocess to simulate __main__ context
    result = subprocess.run(
        [sys.executable, '-c', test_code],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Subprocess failed: {result.stderr}"
    assert "SUCCESS: All imports worked" in result.stdout


def test_main_module_execution():
    """Test the package can be executed as a module."""
    # Get the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Test running as module
    test_code = """
import sys
sys.path.insert(0, r'{}')

# Set __name__ to __main__ to simulate script execution
__name__ = "__main__"

# This should not raise import errors
from chrome_devtools_mcp_fork import get_mcp_server
print("SUCCESS: Module execution context works")
""".format(project_root)
    
    result = subprocess.run(
        [sys.executable, '-c', test_code],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Module execution failed: {result.stderr}"
    assert "SUCCESS: Module execution context works" in result.stdout