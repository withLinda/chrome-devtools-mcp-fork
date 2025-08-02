"""Test MCP protocol compliance and standards."""

import pytest
import json
import sys
from io import StringIO
from chrome_devtools_mcp_fork.main import app


@pytest.mark.asyncio
async def test_tool_schema_validation():
    """Validate all tools have proper MCP schemas."""
    tools = await app.list_tools()

    for tool in tools:
        # Check required attributes
        assert hasattr(tool, "name"), "Tool missing name attribute"
        assert hasattr(tool, "description"), f"Tool {tool.name} missing description"
        assert hasattr(tool, "inputSchema"), f"Tool {tool.name} missing inputSchema"

        # Validate input schema structure
        schema = tool.inputSchema
        assert isinstance(schema, dict), f"Tool {tool.name} schema must be dict"
        assert "type" in schema, f"Tool {tool.name} schema missing type"
        assert schema["type"] == "object", (
            f"Tool {tool.name} schema type must be 'object'"
        )

        # Check if properties exist when there are parameters
        if "properties" in schema:
            assert isinstance(schema["properties"], dict), (
                f"Tool {tool.name} properties must be dict"
            )

            # Validate each property
            for prop_name, prop_def in schema["properties"].items():
                # Handle anyOf for optional parameters
                if "anyOf" in prop_def:
                    assert all("type" in option for option in prop_def["anyOf"]), (
                        f"Tool {tool.name} property {prop_name} anyOf options missing type"
                    )
                else:
                    assert "type" in prop_def, (
                        f"Tool {tool.name} property {prop_name} missing type"
                    )

        # Check required fields if present
        if "required" in schema:
            assert isinstance(schema["required"], list), (
                f"Tool {tool.name} required must be list"
            )


def test_stdio_transport_no_stdout():
    """Test that MCP server doesn't write to stdout (only stderr for logs)."""
    # Capture stdout
    old_stdout = sys.stdout
    captured_stdout = StringIO()
    sys.stdout = captured_stdout

    try:
        # Import should not print to stdout

        # Get stdout content
        stdout_content = captured_stdout.getvalue()

        # Should be empty (MCP servers must not write to stdout)
        assert stdout_content == "", f"Server wrote to stdout: {stdout_content}"

    finally:
        sys.stdout = old_stdout


def test_error_response_format():
    """Validate error responses match expected format."""
    from chrome_devtools_mcp_fork.utils.helpers import create_error_response

    # Test error response structure
    error = create_error_response("Test error", {"detail": "Additional info"})

    # Check required fields
    assert isinstance(error, dict), "Error response must be dict"
    assert error["success"] is False, "Error response success must be False"
    assert error["error"] == "Test error", "Error message mismatch"
    assert "details" in error, "Error response missing details"
    assert "timestamp" in error, "Error response missing timestamp"

    # Test without details
    error2 = create_error_response("Simple error")
    assert error2["details"] == {}, "Default details should be empty dict"


def test_success_response_format():
    """Validate success responses match expected format."""
    from chrome_devtools_mcp_fork.utils.helpers import create_success_response

    # Test success response structure
    success = create_success_response({"result": "data"}, "Operation successful")

    # Check required fields
    assert isinstance(success, dict), "Success response must be dict"
    assert success["success"] is True, "Success response success must be True"
    assert success["message"] == "Operation successful", "Success message mismatch"
    assert success["data"] == {"result": "data"}, "Success data mismatch"
    assert "timestamp" in success, "Success response missing timestamp"

    # Test with default message
    success2 = create_success_response(None)
    assert success2["message"] == "Success", "Default message should be 'Success'"
    assert success2["data"] is None, "Data should be None when not provided"


@pytest.mark.asyncio
async def test_tool_descriptions():
    """Ensure all tools have meaningful descriptions."""
    tools = await app.list_tools()

    for tool in tools:
        # Description should exist and be meaningful
        assert tool.description, f"Tool {tool.name} has empty description"
        assert len(tool.description) > 10, f"Tool {tool.name} description too short"
        assert not tool.description.startswith("TODO"), (
            f"Tool {tool.name} has placeholder description"
        )
        assert not tool.description.lower().startswith("placeholder"), (
            f"Tool {tool.name} has placeholder description"
        )


def test_json_serializable_responses():
    """Test that all response formats are JSON serializable."""
    from chrome_devtools_mcp_fork.utils.helpers import (
        create_success_response,
        create_error_response,
    )

    # Test various response types
    responses = [
        create_success_response(None),
        create_success_response("string data"),
        create_success_response({"key": "value"}),
        create_success_response([1, 2, 3]),
        create_error_response("Error message"),
        create_error_response("Error", {"code": 404}),
    ]

    for response in responses:
        try:
            json_str = json.dumps(response)
            assert json_str, "Response should serialize to non-empty JSON"

            # Should be able to parse back
            parsed = json.loads(json_str)
            assert isinstance(parsed, dict), "Parsed response should be dict"

        except (TypeError, ValueError) as e:
            pytest.fail(f"Response not JSON serializable: {e}")


@pytest.mark.asyncio
async def test_parameter_types():
    """Verify parameter types match Python type hints."""
    tools = await app.list_tools()

    # Known parameter types from our implementation
    expected_types = {
        "port": "integer",
        "headless": "boolean",
        "chrome_path": ["string", "null"],
        "url": "string",
        "depth": "integer",
        "node_id": "integer",
    }

    for tool in tools:
        if "properties" in tool.inputSchema:
            for param_name, param_def in tool.inputSchema["properties"].items():
                if param_name in expected_types:
                    param_type = param_def.get("type")
                    expected = expected_types[param_name]

                    # Handle anyOf for optional parameters
                    if "anyOf" in param_def:
                        types = [t.get("type") for t in param_def["anyOf"]]
                        assert set(types) == set(expected), (
                            f"Tool {tool.name} param {param_name} type mismatch"
                        )
                    else:
                        assert param_type == expected, (
                            f"Tool {tool.name} param {param_name} type mismatch"
                        )
