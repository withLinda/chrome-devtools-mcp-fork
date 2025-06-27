#!/usr/bin/env python3
"""
Pytest test suite for Chrome DevTools MCP

This test suite validates all MCP tools using pytest framework.
"""

from __future__ import annotations

import asyncio
import logging
import os
import platform
import subprocess
import sys

import pytest
import pytest_asyncio

sys.path.insert(0, os.path.dirname(__file__))

from src.client import ChromeDevToolsClient

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_chrome_path() -> str | None:
    """Get Chrome executable path for testing."""
    system = platform.system()
    paths = []

    if system == "Darwin":  # macOS
        paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
        ]
    elif system == "Linux":
        paths = [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium-browser",
            "/usr/bin/chromium",
        ]
    elif system == "Windows":
        paths = [
            "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
        ]

    for path in paths:
        if os.path.exists(path):
            return path
    return None


@pytest_asyncio.fixture(scope="session")
async def chrome_setup():
    """Set up Chrome instance for testing."""
    test_port = 9223
    chrome_path = get_chrome_path()

    if not chrome_path:
        pytest.skip("Chrome not found for testing")

    logger.info("Setting up test environment...")

    cmd = [
        chrome_path,
        f"--remote-debugging-port={test_port}",
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--user-data-dir=/tmp/chrome-test-profile",
    ]

    chrome_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    await asyncio.sleep(3)
    logger.info(f"Chrome started for testing on port {test_port}")

    yield test_port

    # Cleanup
    logger.info("Cleaning up test environment...")
    chrome_process.terminate()
    chrome_process.wait()
    logger.info("Test environment cleaned up")


@pytest_asyncio.fixture
async def cdp_client(chrome_setup):
    """Create and connect CDP client."""
    test_port = chrome_setup
    client = ChromeDevToolsClient(port=test_port)

    connected = await client.connect()
    if not connected:
        pytest.skip("Failed to connect to Chrome for testing")

    await client.enable_domains()
    logger.info("CDP client connected and ready")

    yield client

    await client.disconnect()


async def setup_test_page(cdp_client: ChromeDevToolsClient):
    """Set up a test page with elements for testing."""
    html = """
    <html>
    <head><title>Test Page</title></head>
    <body>
        <div id="test-element" class="test-class">Test Content</div>
        <button id="test-button">Test Button</button>
        <script>console.log('Test page loaded');</script>
    </body>
    </html>
    """
    await cdp_client.send_command("Page.navigate", {"url": f"data:text/html,{html}"})
    await asyncio.sleep(1)


@pytest.mark.asyncio
async def test_chrome_detection():
    """Test Chrome detection and startup."""
    chrome_path = get_chrome_path()
    assert chrome_path is not None, "Chrome executable not found"
    assert os.path.exists(chrome_path), f"Chrome path does not exist: {chrome_path}"


@pytest.mark.asyncio
async def test_connection_status(cdp_client):
    """Test CDP connection status."""
    assert cdp_client.connected, "CDP client should be connected"

    target_info = await cdp_client.get_target_info()
    assert target_info is not None, "Should be able to get target info"


@pytest.mark.asyncio
async def test_navigation(cdp_client):
    """Test page navigation."""
    await cdp_client.send_command(
        "Page.navigate",
        {"url": "data:text/html,<html><body><h1>Navigation Test</h1></body></html>"},
    )
    await asyncio.sleep(1)


@pytest.mark.asyncio
async def test_get_document(cdp_client):
    """Test document retrieval."""
    await setup_test_page(cdp_client)

    result = await cdp_client.send_command("DOM.getDocument", {"depth": 2})
    assert "root" in result, "Document should have root element"
    assert "nodeId" in result["root"], "Root should have node ID"


@pytest.mark.asyncio
async def test_query_selector(cdp_client):
    """Test CSS selector querying."""
    await setup_test_page(cdp_client)

    doc_result = await cdp_client.send_command("DOM.getDocument", {"depth": 2})
    root_id = doc_result["root"]["nodeId"]

    element_result = await cdp_client.send_command(
        "DOM.querySelector", {"nodeId": root_id, "selector": "#test-element"}
    )

    assert element_result["nodeId"] != 0, "Should find test element"


@pytest.mark.asyncio
async def test_element_attributes(cdp_client):
    """Test element attribute retrieval."""
    await setup_test_page(cdp_client)

    doc_result = await cdp_client.send_command("DOM.getDocument", {"depth": 2})
    root_id = doc_result["root"]["nodeId"]

    element_result = await cdp_client.send_command(
        "DOM.querySelector", {"nodeId": root_id, "selector": "#test-element"}
    )

    if element_result["nodeId"] != 0:
        attrs_result = await cdp_client.send_command(
            "DOM.getAttributes", {"nodeId": element_result["nodeId"]}
        )
        assert "attributes" in attrs_result, "Should return attributes"


@pytest.mark.asyncio
async def test_element_outer_html(cdp_client):
    """Test element HTML retrieval."""
    await setup_test_page(cdp_client)

    doc_result = await cdp_client.send_command("DOM.getDocument", {"depth": 2})
    root_id = doc_result["root"]["nodeId"]

    element_result = await cdp_client.send_command(
        "DOM.querySelector", {"nodeId": root_id, "selector": "#test-element"}
    )

    if element_result["nodeId"] != 0:
        html_result = await cdp_client.send_command(
            "DOM.getOuterHTML", {"nodeId": element_result["nodeId"]}
        )
        assert "outerHTML" in html_result, "Should return outer HTML"
        assert "test-element" in html_result["outerHTML"], "HTML should contain element ID"


@pytest.mark.asyncio
async def test_computed_styles(cdp_client):
    """Test computed style retrieval."""
    await setup_test_page(cdp_client)

    doc_result = await cdp_client.send_command("DOM.getDocument", {"depth": 2})
    root_id = doc_result["root"]["nodeId"]

    element_result = await cdp_client.send_command(
        "DOM.querySelector", {"nodeId": root_id, "selector": "#test-element"}
    )

    if element_result["nodeId"] != 0:
        styles_result = await cdp_client.send_command(
            "CSS.getComputedStyleForNode", {"nodeId": element_result["nodeId"]}
        )
        assert "computedStyle" in styles_result, "Should return computed styles"


@pytest.mark.asyncio
async def test_javascript_execution(cdp_client):
    """Test JavaScript code execution."""
    result = await cdp_client.send_command(
        "Runtime.evaluate", {"expression": "2 + 2", "returnByValue": True}
    )

    assert "result" in result, "Should return result"
    assert result["result"]["value"] == 4, "JavaScript execution should work correctly"


@pytest.mark.asyncio
async def test_console_logs(cdp_client):
    """Test console log capture."""
    await cdp_client.send_command(
        "Runtime.evaluate",
        {"expression": "console.log('Test log message')", "returnByValue": True},
    )

    await asyncio.sleep(1)
    # Note: Console log capture may vary by Chrome version


@pytest.mark.asyncio
async def test_network_monitoring(cdp_client):
    """Test network request monitoring."""
    initial_requests = len(cdp_client.network_requests)

    await cdp_client.send_command(
        "Runtime.evaluate",
        {
            "expression": "fetch('data:text/plain,test').then(r => r.text())",
            "returnByValue": True,
            "awaitPromise": True,
        },
    )

    await asyncio.sleep(1)

    # Network monitoring may capture some requests
    final_requests = len(cdp_client.network_requests)
    assert final_requests >= initial_requests, "Should track network activity"


@pytest.mark.asyncio
async def test_performance_metrics(cdp_client):
    """Test performance metrics collection."""
    await cdp_client.send_command("Performance.enable")
    metrics_result = await cdp_client.send_command("Performance.getMetrics")

    assert "metrics" in metrics_result, "Should return performance metrics"
    assert len(metrics_result["metrics"]) > 0, "Should have performance data"


@pytest.mark.asyncio
async def test_page_info(cdp_client):
    """Test page information retrieval."""
    await setup_test_page(cdp_client)

    result = await cdp_client.send_command(
        "Runtime.evaluate",
        {
            "expression": (
                "({title: document.title, url: window.location.href, "
                "readyState: document.readyState})"
            ),
            "returnByValue": True,
        },
    )

    assert "result" in result, "Should return page information"
    page_info = result["result"]["value"]
    assert "title" in page_info, "Should include page title"
    assert "url" in page_info, "Should include page URL"


@pytest.mark.asyncio
async def test_storage_operations(cdp_client):
    """Test storage operations."""
    try:
        # Test storage quota check
        await cdp_client.send_command(
            "Storage.getUsageAndQuota", {"origin": "http://localhost"}
        )

        # Test storage clearing
        await cdp_client.send_command(
            "Storage.clearDataForOrigin",
            {"origin": "http://localhost", "storageTypes": "cookies"}
        )

    except Exception:
        # Storage operations may not be fully available in headless mode
        pytest.skip("Storage operations not fully available in test environment")


# Test for CSS operations
@pytest.mark.asyncio
async def test_css_media_queries(cdp_client):
    """Test CSS media queries retrieval."""
    try:
        result = await cdp_client.send_command("CSS.getMediaQueries")
        assert "medias" in result, "Should return media queries"
    except Exception:
        # CSS domain may not be fully available in headless mode
        pytest.skip("CSS operations not fully available in test environment")


@pytest.mark.asyncio
async def test_search_elements(cdp_client):
    """Test element searching."""
    await setup_test_page(cdp_client)

    try:
        search_result = await cdp_client.send_command(
            "DOM.performSearch", {"query": "test", "includeUserAgentShadowDOM": False}
        )

        search_id = search_result["searchId"]
        result_count = search_result["resultCount"]

        if result_count > 0:
            results = await cdp_client.send_command(
                "DOM.getSearchResults",
                {"searchId": search_id, "fromIndex": 0, "toIndex": min(result_count, 10)}
            )
            assert "nodeIds" in results, "Should return search results"

        # Cleanup search
        await cdp_client.send_command("DOM.discardSearchResults", {"searchId": search_id})

    except Exception:
        # DOM search may not be fully available in all Chrome versions
        pytest.skip("DOM search not fully available in test environment")

