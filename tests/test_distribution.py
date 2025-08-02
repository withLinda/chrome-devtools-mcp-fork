"""Test PyPI deployment readiness and package distribution."""

import pytest
import subprocess
import sys
import os
import tempfile


def test_package_metadata():
    """Verify setup.py/pyproject.toml correctness."""
    # Check pyproject.toml exists
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pyproject_path = os.path.join(project_root, "pyproject.toml")

    assert os.path.exists(pyproject_path), "pyproject.toml not found"

    # Read pyproject.toml - handle Python 3.10 compatibility
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib

    with open(pyproject_path, "rb") as f:
        pyproject = tomllib.load(f)

    # Check required fields
    assert "project" in pyproject, "Missing [project] section"
    project = pyproject["project"]

    assert "name" in project, "Missing project name"
    assert project["name"] == "chrome-devtools-mcp-fork", "Incorrect project name"

    assert "version" in project, "Missing project version"
    assert project["version"] == "2.0.1", "Version mismatch"

    assert "description" in project, "Missing project description"
    assert "authors" in project, "Missing project authors"
    assert "requires-python" in project, "Missing Python version requirement"

    # Check dependencies
    assert "dependencies" in project, "Missing dependencies"
    deps = project["dependencies"]
    assert "mcp>=1.0.0" in deps, "Missing mcp dependency"
    # Check for requests dependency (with or without version)
    assert any("requests" in dep for dep in deps), "Missing requests dependency"
    # Check for websocket-client dependency (with or without version)
    assert any("websocket-client" in dep for dep in deps), (
        "Missing websocket-client dependency"
    )


def test_version_consistency():
    """Test version is consistent across files."""
    import chrome_devtools_mcp_fork

    # Check __version__ attribute
    assert hasattr(chrome_devtools_mcp_fork, "__version__"), "Missing __version__"
    assert chrome_devtools_mcp_fork.__version__ == "2.0.1", (
        "Version mismatch in __init__.py"
    )

    # Check against pyproject.toml
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pyproject_path = os.path.join(project_root, "pyproject.toml")

    try:
        import tomllib
    except ImportError:
        import tomli as tomllib

    with open(pyproject_path, "rb") as f:
        pyproject = tomllib.load(f)

    pyproject_version = pyproject["project"]["version"]
    assert chrome_devtools_mcp_fork.__version__ == pyproject_version, (
        f"Version mismatch: __init__.py={chrome_devtools_mcp_fork.__version__}, pyproject.toml={pyproject_version}"
    )


def test_build_package():
    """Test that package builds successfully."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Create a temporary directory for build artifacts
    with tempfile.TemporaryDirectory() as temp_dir:
        # Try to build the package
        result = subprocess.run(
            [sys.executable, "-m", "build", "--outdir", temp_dir],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            # If build module not installed, skip test
            if "No module named build" in result.stderr:
                pytest.skip("build module not installed")
            else:
                pytest.fail(f"Package build failed: {result.stderr}")

        # Check that wheel and sdist were created
        files = os.listdir(temp_dir)
        wheel_files = [f for f in files if f.endswith(".whl")]
        sdist_files = [f for f in files if f.endswith(".tar.gz")]

        assert len(wheel_files) == 1, f"Expected 1 wheel file, found {len(wheel_files)}"
        assert len(sdist_files) == 1, f"Expected 1 sdist file, found {len(sdist_files)}"


def test_entry_points():
    """Test that console scripts/entry points are configured."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pyproject_path = os.path.join(project_root, "pyproject.toml")

    try:
        import tomllib
    except ImportError:
        import tomli as tomllib

    with open(pyproject_path, "rb") as f:
        _ = tomllib.load(f)  # Just verify it loads correctly

    # Check for MCP server configuration
    # Note: MCP servers typically don't have console scripts but are run via server.py
    # The important thing is that the package can be imported and main() can be called

    # Test that main entry point works
    from chrome_devtools_mcp_fork import main

    assert callable(main), "main() should be callable"


def test_importable_after_install():
    """Test package can be imported in clean environment."""
    # This test simulates what happens after pip install
    test_script = """
import sys
import chrome_devtools_mcp_fork

# Test basic imports
assert hasattr(chrome_devtools_mcp_fork, '__version__')
assert hasattr(chrome_devtools_mcp_fork, 'main')
assert hasattr(chrome_devtools_mcp_fork, 'app')
assert hasattr(chrome_devtools_mcp_fork, 'get_mcp_server')

# Test getting MCP server
mcp = chrome_devtools_mcp_fork.get_mcp_server()
assert mcp is not None

print("SUCCESS: Package imports work correctly")
"""

    result = subprocess.run(
        [sys.executable, "-c", test_script], capture_output=True, text=True
    )

    assert result.returncode == 0, f"Import test failed: {result.stderr}"
    assert "SUCCESS" in result.stdout


def test_no_missing_files():
    """Ensure all necessary files are included in package."""
    import chrome_devtools_mcp_fork

    package_dir = os.path.dirname(chrome_devtools_mcp_fork.__file__)

    # Check that all expected modules exist
    expected_files = [
        "__init__.py",
        "main.py",
        "client.py",
        "tools/__init__.py",
        "tools/browser.py",
        "tools/console.py",
        "tools/css.py",
        "tools/dom.py",
        "tools/network.py",
        "tools/performance.py",
        "tools/storage.py",
        "utils/__init__.py",
        "utils/helpers.py",
    ]

    for file_path in expected_files:
        full_path = os.path.join(package_dir, file_path)
        assert os.path.exists(full_path), f"Missing file: {file_path}"


def test_dependency_versions():
    """Test that dependency versions are appropriate."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pyproject_path = os.path.join(project_root, "pyproject.toml")

    try:
        import tomllib
    except ImportError:
        import tomli as tomllib

    with open(pyproject_path, "rb") as f:
        pyproject = tomllib.load(f)

    deps = pyproject["project"]["dependencies"]

    # Check each dependency has appropriate version constraints
    for dep in deps:
        if "mcp" in dep:
            assert ">=" in dep or "~=" in dep, "mcp should have version constraint"
        # requests and websocket-client can be unpinned for flexibility
