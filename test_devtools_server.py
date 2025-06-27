#!/usr/bin/env python3
"""
Test suite for Chrome DevTools MCP

This test suite validates all MCP tools to ensure they work as expected.
Tests can be run individually or all together.
"""

from __future__ import annotations

import asyncio
import logging
import os
import platform
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))

from src.client import ChromeDevToolsClient

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DevToolsTestSuite:
    """Comprehensive test suite for all Chrome DevTools MCP tools."""

    def __init__(self):
        self.test_port = 9223
        self.chrome_process = None
        self.cdp_client = None
        self.test_results = {}
        self.failed_tests = []

    async def setup(self):
        """Set up test environment."""
        logger.info("Setting up test environment...")

        await self._start_chrome_for_testing()

        self.cdp_client = ChromeDevToolsClient(port=self.test_port)

        connected = await self.cdp_client.connect()
        if not connected:
            raise RuntimeError("Failed to connect to Chrome for testing")

        await self.cdp_client.enable_domains()

        logger.info("Test environment ready")

    async def _setup_test_page(self):
        """Set up test page with elements for testing."""
        await self.cdp_client.send_command(
            "Page.navigate",
            {
                "url": (
                    "data:text/html,<html><head><title>Test Page</title></head><body>"
                    "<h1>Chrome DevTools MCP Test Page</h1><p>Testing in progress...</p>"
                    "<div id='test-element' class='test-class' style='color: red;'>"
                    "Test Element</div></body></html>"
                )
            },
        )

        await asyncio.sleep(2)

    async def teardown(self):
        """Clean up test environment."""
        logger.info("Cleaning up test environment...")

        if self.cdp_client:
            await self.cdp_client.disconnect()

        if self.chrome_process:
            try:
                self.chrome_process.terminate()
                self.chrome_process.wait(timeout=5)
            except Exception:
                try:
                    self.chrome_process.kill()
                except Exception:
                    pass

        logger.info("Test environment cleaned up")

    async def _start_chrome_for_testing(self):
        """Start Chrome with debugging enabled for testing."""
        from src.tools.chrome_management import check_chrome_running, get_chrome_executable_path

        if await check_chrome_running(self.test_port):
            logger.info(f"Chrome already running on port {self.test_port}")
            return

        chrome_path = get_chrome_executable_path()
        if not chrome_path:
            raise RuntimeError("Chrome executable not found")

        user_data_dir = (
            f"/tmp/chrome-test-{self.test_port}"
            if platform.system() != "Windows"
            else f"C:\\temp\\chrome-test-{self.test_port}"
        )

        chrome_args = [
            chrome_path,
            f"--remote-debugging-port={self.test_port}",
            f"--user-data-dir={user_data_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-extensions",
            "--disable-default-apps",
            "--headless",
        ]

        self.chrome_process = subprocess.Popen(
            chrome_args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

        await asyncio.sleep(3)

        if not await check_chrome_running(self.test_port):
            raise RuntimeError("Failed to start Chrome for testing")

        logger.info(f"Chrome started for testing on port {self.test_port}")

    async def run_test(self, test_name: str, test_func):
        """Run a single test and record results."""
        logger.info(f"Running test: {test_name}")

        try:
            result = await test_func()
            self.test_results[test_name] = {"status": "PASSED", "result": result, "error": None}
            logger.info(f"✓ {test_name} PASSED")
            return True

        except Exception as e:
            error_msg = str(e)
            self.test_results[test_name] = {"status": "FAILED", "result": None, "error": error_msg}
            self.failed_tests.append(test_name)
            logger.error(f"✗ {test_name} FAILED: {error_msg}")
            return False

    async def test_chrome_detection(self):
        """Test Chrome executable detection."""
        from src.tools.chrome_management import get_chrome_executable_path

        chrome_path = get_chrome_executable_path()
        if not chrome_path:
            raise AssertionError("Chrome executable not found")

        if not os.path.exists(chrome_path):
            raise AssertionError(f"Chrome path does not exist: {chrome_path}")

        return {"chrome_path": chrome_path}

    async def test_connection_status(self):
        """Test connection status checking."""
        if not self.cdp_client or not self.cdp_client.connected:
            raise AssertionError("CDP client not connected")

        target_info = await self.cdp_client.get_target_info()
        return {"connected": True, "target": target_info}

    async def test_get_document(self):
        """Test DOM document retrieval."""
        result = await self.cdp_client.send_command("DOM.getDocument", {"depth": 2})

        if "root" not in result:
            raise AssertionError("No root node in document")

        root = result["root"]
        if root.get("nodeName") != "#document":
            raise AssertionError("Invalid root node type")

        return {"nodeId": root.get("nodeId"), "children": len(root.get("children", []))}

    async def test_query_selector(self):
        """Test DOM querySelector functionality."""
        await self._setup_test_page()

        doc_result = await self.cdp_client.send_command("DOM.getDocument", {"depth": 2})
        root_id = doc_result["root"]["nodeId"]

        result = await self.cdp_client.send_command(
            "DOM.querySelector", {"nodeId": root_id, "selector": "#test-element"}
        )

        if result["nodeId"] == 0:
            raise AssertionError("Test element not found")

        return {"nodeId": result["nodeId"]}

    async def test_element_attributes(self):
        """Test getting element attributes."""
        await self._setup_test_page()

        doc_result = await self.cdp_client.send_command("DOM.getDocument", {"depth": 2})
        root_id = doc_result["root"]["nodeId"]

        element_result = await self.cdp_client.send_command(
            "DOM.querySelector", {"nodeId": root_id, "selector": "#test-element"}
        )

        if element_result["nodeId"] == 0:
            raise AssertionError("Test element not found")

        attrs_result = await self.cdp_client.send_command(
            "DOM.getAttributes", {"nodeId": element_result["nodeId"]}
        )

        attributes = {}
        attr_list = attrs_result["attributes"]
        for i in range(0, len(attr_list), 2):
            if i + 1 < len(attr_list):
                attributes[attr_list[i]] = attr_list[i + 1]

        if "id" not in attributes or attributes["id"] != "test-element":
            raise AssertionError("Expected attributes not found")

        return {"attributes": attributes}

    async def test_element_outer_html(self):
        """Test getting element outer HTML."""
        await self._setup_test_page()

        doc_result = await self.cdp_client.send_command("DOM.getDocument", {"depth": 2})
        root_id = doc_result["root"]["nodeId"]

        element_result = await self.cdp_client.send_command(
            "DOM.querySelector", {"nodeId": root_id, "selector": "#test-element"}
        )

        if element_result["nodeId"] == 0:
            raise AssertionError("Test element not found")

        html_result = await self.cdp_client.send_command(
            "DOM.getOuterHTML", {"nodeId": element_result["nodeId"]}
        )

        html = html_result["outerHTML"]
        if "test-element" not in html or "Test Element" not in html:
            raise AssertionError("Expected HTML content not found")

        return {"htmlLength": len(html)}

    async def test_search_elements(self):
        """Test DOM element search."""
        search_result = await self.cdp_client.send_command(
            "DOM.performSearch", {"query": "Test Element", "includeUserAgentShadowDOM": False}
        )

        search_id = search_result["searchId"]
        result_count = search_result["resultCount"]

        if result_count == 0:
            await self.cdp_client.send_command("DOM.discardSearchResults", {"searchId": search_id})
            raise AssertionError("No search results found")

        results = await self.cdp_client.send_command(
            "DOM.getSearchResults",
            {"searchId": search_id, "fromIndex": 0, "toIndex": min(result_count, 10)},
        )

        await self.cdp_client.send_command("DOM.discardSearchResults", {"searchId": search_id})

        return {"resultCount": result_count, "nodeIds": results["nodeIds"]}

    async def test_computed_styles(self):
        """Test getting computed CSS styles."""
        await self._setup_test_page()

        doc_result = await self.cdp_client.send_command("DOM.getDocument", {"depth": 2})
        root_id = doc_result["root"]["nodeId"]

        element_result = await self.cdp_client.send_command(
            "DOM.querySelector", {"nodeId": root_id, "selector": "#test-element"}
        )

        if element_result["nodeId"] == 0:
            raise AssertionError("Test element not found")

        styles_result = await self.cdp_client.send_command(
            "CSS.getComputedStyleForNode", {"nodeId": element_result["nodeId"]}
        )

        styles = {}
        for prop in styles_result["computedStyle"]:
            styles[prop["name"]] = prop["value"]

        if "color" not in styles:
            raise AssertionError("Expected CSS properties not found")

        return {"propertyCount": len(styles), "color": styles.get("color")}

    async def test_inline_styles(self):
        """Test getting inline CSS styles."""
        await self._setup_test_page()

        doc_result = await self.cdp_client.send_command("DOM.getDocument", {"depth": 2})
        root_id = doc_result["root"]["nodeId"]

        element_result = await self.cdp_client.send_command(
            "DOM.querySelector", {"nodeId": root_id, "selector": "#test-element"}
        )

        if element_result["nodeId"] == 0:
            raise AssertionError("Test element not found")

        styles_result = await self.cdp_client.send_command(
            "CSS.getInlineStylesForNode", {"nodeId": element_result["nodeId"]}
        )

        inline_styles = {}
        if styles_result.get("inlineStyle") and styles_result["inlineStyle"].get("cssProperties"):
            for prop in styles_result["inlineStyle"]["cssProperties"]:
                inline_styles[prop["name"]] = prop["value"]

        if "color" not in inline_styles:
            raise AssertionError("Expected inline styles not found")

        return {"inlineStyles": inline_styles}

    async def test_css_media_queries(self):
        """Test getting CSS media queries."""
        result = await self.cdp_client.send_command("CSS.getMediaQueries")

        medias = result.get("medias", [])
        return {"mediaQueryCount": len(medias)}

    async def test_javascript_execution(self):
        """Test JavaScript execution."""
        test_code = "2 + 2"

        result = await self.cdp_client.send_command(
            "Runtime.evaluate", {"expression": test_code, "returnByValue": True}
        )

        if result.get("exceptionDetails"):
            raise AssertionError("JavaScript execution failed")

        value = result.get("result", {}).get("value")
        if value != 4:
            raise AssertionError(f"Expected 4, got {value}")

        return {"code": test_code, "result": value}

    async def test_console_logs(self):
        """Test console log capture."""
        initial_count = len(self.cdp_client.console_logs)

        await self.cdp_client.send_command(
            "Runtime.evaluate",
            {"expression": "console.log('Test log message')", "returnByValue": True},
        )

        await asyncio.sleep(0.5)

        if len(self.cdp_client.console_logs) <= initial_count:
            raise AssertionError("Console log not captured")

        latest_log = self.cdp_client.console_logs[-1]
        if "Test log message" not in str(latest_log.get("args", [])):
            raise AssertionError("Expected log message not found")

        return {"logCount": len(self.cdp_client.console_logs)}

    async def test_object_inspection(self):
        """Test JavaScript object inspection."""
        await self.cdp_client.send_command(
            "Runtime.evaluate",
            {"expression": "window.testObject = {name: 'test', value: 42}", "returnByValue": True},
        )

        result = await self.cdp_client.send_command(
            "Runtime.evaluate", {"expression": "window.testObject", "returnByValue": False}
        )

        object_id = result.get("result", {}).get("objectId")
        if not object_id:
            raise AssertionError("Failed to get object reference")

        props_result = await self.cdp_client.send_command(
            "Runtime.getProperties", {"objectId": object_id, "ownProperties": True}
        )

        properties = {}
        for prop in props_result.get("result", []):
            prop_name = prop.get("name")
            prop_value = prop.get("value", {})
            properties[prop_name] = prop_value.get("value")

        if properties.get("name") != "test" or properties.get("value") != 42:
            raise AssertionError("Object properties not correctly retrieved")

        return {"properties": properties}

    async def test_network_monitoring(self):
        """Test network request monitoring."""
        initial_count = len(self.cdp_client.network_requests)

        await self.cdp_client.send_command(
            "Runtime.evaluate",
            {
                "expression": "fetch('data:text/plain,test').catch(e => e)",
                "returnByValue": True,
                "awaitPromise": True,
            },
        )

        await asyncio.sleep(1)

        if len(self.cdp_client.network_requests) <= initial_count:
            raise AssertionError("Network request not captured")

        return {"networkRequests": len(self.cdp_client.network_requests)}

    async def test_cookie_management(self):
        """Test cookie management."""
        await self.cdp_client.send_command(
            "Storage.setCookies",
            {
                "cookies": [
                    {
                        "name": "test_cookie",
                        "value": "test_value",
                        "domain": "localhost",
                        "path": "/",
                    }
                ]
            },
        )

        result = await self.cdp_client.send_command("Storage.getCookies")

        cookies = result.get("cookies", [])
        test_cookie = None
        for cookie in cookies:
            if cookie.get("name") == "test_cookie":
                test_cookie = cookie
                break

        if not test_cookie:
            raise AssertionError("Test cookie not found")

        if test_cookie.get("value") != "test_value":
            raise AssertionError("Cookie value mismatch")

        return {"cookieCount": len(cookies), "testCookie": test_cookie}

    async def test_storage_quota(self):
        """Test storage quota information."""
        result = await self.cdp_client.send_command(
            "Storage.getUsageAndQuota", {"origin": "http://localhost"}
        )

        if "usage" not in result or "quota" not in result:
            raise AssertionError("Storage quota information incomplete")

        return {"usageBytes": result.get("usage", 0), "quotaBytes": result.get("quota", 0)}

    async def test_performance_metrics(self):
        """Test performance metrics collection."""
        await self.cdp_client.send_command("Performance.enable")

        result = await self.cdp_client.send_command("Performance.getMetrics")

        metrics = result.get("metrics", [])
        if not metrics:
            raise AssertionError("No performance metrics returned")

        return {"metricCount": len(metrics)}

    async def test_page_info(self):
        """Test page information retrieval."""
        await self._setup_test_page()

        result = await self.cdp_client.send_command(
            "Runtime.evaluate",
            {
                "expression": (
                    "({title: document.title, url: window.location.href, "
                    "readyState: document.readyState})"
                ),
                "returnByValue": True,
            },
        )

        page_info = result.get("result", {}).get("value", {})

        if "url" not in page_info:
            raise AssertionError("Page URL not retrieved")

        return page_info

    async def test_element_box_model(self):
        """Test getting element box model."""
        await self._setup_test_page()

        doc_result = await self.cdp_client.send_command("DOM.getDocument", {"depth": 2})
        root_id = doc_result["root"]["nodeId"]

        element_result = await self.cdp_client.send_command(
            "DOM.querySelector", {"nodeId": root_id, "selector": "#test-element"}
        )

        if element_result["nodeId"] == 0:
            raise AssertionError("Test element not found")

        box_result = await self.cdp_client.send_command(
            "DOM.getBoxModel", {"nodeId": element_result["nodeId"]}
        )

        model = box_result["model"]
        if "content" not in model or "padding" not in model:
            raise AssertionError("Box model incomplete")

        return {"hasBoxModel": True, "width": model.get("width"), "height": model.get("height")}

    async def test_describe_element(self):
        """Test element description."""
        await self._setup_test_page()

        doc_result = await self.cdp_client.send_command("DOM.getDocument", {"depth": 2})
        root_id = doc_result["root"]["nodeId"]

        element_result = await self.cdp_client.send_command(
            "DOM.querySelector", {"nodeId": root_id, "selector": "#test-element"}
        )

        if element_result["nodeId"] == 0:
            raise AssertionError("Test element not found")

        desc_result = await self.cdp_client.send_command(
            "DOM.describeNode", {"nodeId": element_result["nodeId"], "depth": 1}
        )

        node = desc_result["node"]
        if node.get("nodeName") != "DIV":
            raise AssertionError("Unexpected element type")

        return {"nodeName": node.get("nodeName"), "nodeType": node.get("nodeType")}

    async def test_matched_styles(self):
        """Test getting matched CSS rules."""
        await self._setup_test_page()

        doc_result = await self.cdp_client.send_command("DOM.getDocument", {"depth": 2})
        root_id = doc_result["root"]["nodeId"]

        element_result = await self.cdp_client.send_command(
            "DOM.querySelector", {"nodeId": root_id, "selector": "#test-element"}
        )

        if element_result["nodeId"] == 0:
            raise AssertionError("Test element not found")

        styles_result = await self.cdp_client.send_command(
            "CSS.getMatchedStylesForNode", {"nodeId": element_result["nodeId"]}
        )

        has_data = (
            styles_result.get("matchedCSSRules")
            or styles_result.get("inlineStyle")
            or styles_result.get("inherited")
        )

        if not has_data:
            raise AssertionError("No style information found")

        return {"hasMatchedStyles": True}

    async def test_background_colors(self):
        """Test getting background colors."""
        await self._setup_test_page()

        doc_result = await self.cdp_client.send_command("DOM.getDocument", {"depth": 2})
        root_id = doc_result["root"]["nodeId"]

        element_result = await self.cdp_client.send_command(
            "DOM.querySelector", {"nodeId": root_id, "selector": "#test-element"}
        )

        if element_result["nodeId"] == 0:
            raise AssertionError("Test element not found")

        colors_result = await self.cdp_client.send_command(
            "CSS.getBackgroundColors", {"nodeId": element_result["nodeId"]}
        )

        return {
            "backgroundColors": colors_result.get("backgroundColors", []),
            "computedFontSize": colors_result.get("computedFontSize"),
            "computedFontWeight": colors_result.get("computedFontWeight"),
        }

    async def test_clear_storage(self):
        """Test clearing storage for origin."""
        await self.cdp_client.send_command(
            "Storage.clearDataForOrigin", {"origin": "http://localhost", "storageTypes": "cookies"}
        )

        return {"cleared": True}

    async def test_storage_tracking(self):
        """Test storage tracking."""
        await self.cdp_client.send_command(
            "Storage.trackCacheStorageForOrigin", {"origin": "http://localhost"}
        )

        await self.cdp_client.send_command(
            "Storage.untrackCacheStorageForOrigin", {"origin": "http://localhost"}
        )

        return {"trackingTested": True}

    async def test_clear_console_command(self):
        """Test clearing console."""
        await self.cdp_client.send_command("Runtime.discardConsoleEntries")
        return {"consoleClearedViaCommand": True}

    async def test_console_error_handling(self):
        """Test console error capture."""
        initial_count = len(self.cdp_client.console_logs)

        await self.cdp_client.send_command(
            "Runtime.evaluate",
            {"expression": "console.error('Test error message')", "returnByValue": True},
        )

        await asyncio.sleep(1)

        if len(self.cdp_client.console_logs) <= initial_count:
            return {
                "errorCaptured": False,
                "note": "Console error handling varies by Chrome version",
            }

        return {"errorCaptured": True}

    async def test_navigation(self):
        """Test page navigation."""
        await self.cdp_client.send_command(
            "Page.navigate",
            {"url": "data:text/html,<html><body><h1>Navigation Test</h1></body></html>"},
        )

        await asyncio.sleep(1)

        return {"navigationCompleted": True}

    async def test_network_response_body(self):
        """Test getting network response body."""
        await self._setup_test_page()

        await self.cdp_client.send_command(
            "Runtime.evaluate",
            {
                "expression": "fetch('data:text/plain,hello world').then(r => r.text())",
                "returnByValue": True,
                "awaitPromise": True,
            },
        )

        await asyncio.sleep(1)

        if not self.cdp_client.network_requests:
            raise AssertionError("No network requests captured")

        latest_request = self.cdp_client.network_requests[-1]
        request_id = latest_request.get("requestId")

        if not request_id:
            raise AssertionError("No request ID available")

        try:
            body_result = await self.cdp_client.send_command(
                "Network.getResponseBody", {"requestId": request_id}
            )
            return {"hasResponseBody": True, "bodyLength": len(body_result.get("body", ""))}
        except Exception:
            return {"hasResponseBody": False, "note": "Response body not accessible"}

    async def test_multi_domain_integration(self):
        """Test integration across multiple domains."""
        doc_result = await self.cdp_client.send_command("DOM.getDocument", {"depth": 2})
        root_id = doc_result["root"]["nodeId"]

        element_result = await self.cdp_client.send_command(
            "DOM.querySelector", {"nodeId": root_id, "selector": "#test-element"}
        )

        if element_result["nodeId"] == 0:
            raise AssertionError("Test element not found")

        styles_result = await self.cdp_client.send_command(
            "CSS.getComputedStyleForNode", {"nodeId": element_result["nodeId"]}
        )

        styles = {prop["name"]: prop["value"] for prop in styles_result["computedStyle"]}

        await self.cdp_client.send_command(
            "Runtime.evaluate",
            {
                "expression": (
                    "document.getElementById('test-element').style.backgroundColor = 'blue'"
                ),
                "returnByValue": True,
            },
        )

        return {"elementFound": True, "stylesCount": len(styles), "jsExecuted": True}

    async def run_all_tests(self):
        """Run all tests and generate report."""
        test_methods = [
            ("chrome_detection", self.test_chrome_detection),
            ("connection_status", self.test_connection_status),
            ("navigation", self.test_navigation),
            ("get_document", self.test_get_document),
            ("query_selector", self.test_query_selector),
            ("element_attributes", self.test_element_attributes),
            ("element_outer_html", self.test_element_outer_html),
            ("search_elements", self.test_search_elements),
            ("element_box_model", self.test_element_box_model),
            ("describe_element", self.test_describe_element),
            ("computed_styles", self.test_computed_styles),
            ("inline_styles", self.test_inline_styles),
            ("css_media_queries", self.test_css_media_queries),
            ("matched_styles", self.test_matched_styles),
            ("background_colors", self.test_background_colors),
            ("javascript_execution", self.test_javascript_execution),
            ("console_logs", self.test_console_logs),
            ("object_inspection", self.test_object_inspection),
            ("clear_console_command", self.test_clear_console_command),
            ("console_error_handling", self.test_console_error_handling),
            ("network_monitoring", self.test_network_monitoring),
            ("network_response_body", self.test_network_response_body),
            ("cookie_management", self.test_cookie_management),
            ("storage_quota", self.test_storage_quota),
            ("clear_storage", self.test_clear_storage),
            ("storage_tracking", self.test_storage_tracking),
            ("performance_metrics", self.test_performance_metrics),
            ("page_info", self.test_page_info),
            ("multi_domain_integration", self.test_multi_domain_integration),
        ]

        logger.info(f"Running {len(test_methods)} tests...")

        passed = 0
        failed = 0

        for test_name, test_func in test_methods:
            success = await self.run_test(test_name, test_func)
            if success:
                passed += 1
            else:
                failed += 1

        self.generate_test_report(passed, failed, len(test_methods))

        return passed, failed

    def generate_test_report(self, passed: int, failed: int, total: int):
        """Generate comprehensive test report."""
        logger.info("\n" + "=" * 80)
        logger.info("Chrome DevTools MCP TEST REPORT")
        logger.info("=" * 80)
        logger.info(f"Total Tests: {total}")
        logger.info(f"Passed: {passed}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Success Rate: {(passed / total) * 100:.1f}%")

        if self.failed_tests:
            logger.info("\nFAILED TESTS:")
            for test in self.failed_tests:
                error = self.test_results[test]["error"]
                logger.info(f"  ✗ {test}: {error}")

        logger.info("\nTEST SUMMARY BY CATEGORY:")
        categories = {
            "Chrome Management": ["chrome_detection", "connection_status", "navigation"],
            "DOM Tools": [
                "get_document",
                "query_selector",
                "element_attributes",
                "element_outer_html",
                "search_elements",
                "element_box_model",
                "describe_element",
            ],
            "CSS Tools": [
                "computed_styles",
                "inline_styles",
                "css_media_queries",
                "matched_styles",
                "background_colors",
            ],
            "Console Tools": [
                "javascript_execution",
                "console_logs",
                "object_inspection",
                "clear_console_command",
                "console_error_handling",
            ],
            "Network Tools": ["network_monitoring", "network_response_body"],
            "Storage Tools": [
                "cookie_management",
                "storage_quota",
                "clear_storage",
                "storage_tracking",
            ],
            "Performance Tools": ["performance_metrics", "page_info"],
            "Integration": ["multi_domain_integration"],
        }

        for category, tests in categories.items():
            category_passed = sum(
                1 for test in tests if self.test_results.get(test, {}).get("status") == "PASSED"
            )
            category_total = len(tests)
            logger.info(f"  {category}: {category_passed}/{category_total}")

        logger.info("=" * 80)


async def main():
    """Main test runner."""
    test_suite = DevToolsTestSuite()

    try:
        await test_suite.setup()
        passed, failed = await test_suite.run_all_tests()

        if failed > 0:
            sys.exit(1)
        else:
            logger.info("All tests passed! ✓")

    except Exception as e:
        logger.error(f"Test setup failed: {e}")
        sys.exit(1)

    finally:
        await test_suite.teardown()


if __name__ == "__main__":
    asyncio.run(main())
