import pytest
from registry import ToolRegistry

def test_dynamic_discovery():
    test_registry = ToolRegistry()
    test_registry.discover_tools()

    assert "echo_test" in test_registry.tools
    meta = test_registry.get_tool_metadata("echo_test")
    assert meta.name == "echo_test"
    assert meta.risk_level == "read"
    assert "message" in meta.input_model.model_fields

def test_tool_execution():
    test_registry = ToolRegistry()
    test_registry.discover_tools()

    echo_func = test_registry.tools["echo_test"]
    result = echo_func(message="running tests")
    assert result == {"status" : "success", "echo" : "running tests"}