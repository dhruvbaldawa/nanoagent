"""
ABOUTME: Tests for ToolRegistry class
ABOUTME: Validates tool registration, retrieval, and listing
"""

import pytest

from nanoagent.tools.registry import ToolRegistry


def dummy_sync_tool(query: str) -> str:
    """Dummy sync tool for testing."""
    return f"Result for: {query}"


async def dummy_async_tool(query: str) -> str:
    """Dummy async tool for testing."""
    return f"Async result for: {query}"


def test_register_and_retrieve_sync_tool():
    """Test registering and retrieving a sync tool."""
    registry = ToolRegistry()
    registry.register("search", dummy_sync_tool)

    tool = registry.get("search")
    assert tool is dummy_sync_tool
    assert tool("test") == "Result for: test"


def test_register_and_retrieve_async_tool():
    """Test registering and retrieving an async tool."""
    registry = ToolRegistry()
    registry.register("async_search", dummy_async_tool)

    tool = registry.get("async_search")
    assert tool is dummy_async_tool


def test_get_missing_tool_raises_keyerror():
    """Test that getting a missing tool raises KeyError."""
    registry = ToolRegistry()

    with pytest.raises(KeyError):
        registry.get("nonexistent")


def test_list_names_returns_registered_tools():
    """Test list_names returns all registered tool names."""
    registry = ToolRegistry()
    registry.register("search", dummy_sync_tool)
    registry.register("fetch", dummy_async_tool)

    names = registry.list_names()
    assert set(names) == {"search", "fetch"}


def test_list_names_empty_registry():
    """Test list_names returns empty list for empty registry."""
    registry = ToolRegistry()

    names = registry.list_names()
    assert names == []


def test_register_overwrites_existing_tool():
    """Test that registering with same name overwrites previous tool."""
    registry = ToolRegistry()
    registry.register("search", dummy_sync_tool)
    registry.register("search", dummy_async_tool)

    tool = registry.get("search")
    assert tool is dummy_async_tool


def test_multiple_tools_independent():
    """Test that multiple registered tools are independent."""
    registry = ToolRegistry()
    registry.register("tool1", dummy_sync_tool)
    registry.register("tool2", dummy_async_tool)

    tool1 = registry.get("tool1")
    tool2 = registry.get("tool2")

    assert tool1 is dummy_sync_tool
    assert tool2 is dummy_async_tool


def test_register_rejects_none_value():
    """Test that registering None value raises TypeError."""
    registry = ToolRegistry()

    with pytest.raises(TypeError, match="cannot be None"):
        registry.register("bad_tool", None)  # type: ignore


def test_register_rejects_non_callable():
    """Test that registering non-callable values raises TypeError."""
    registry = ToolRegistry()

    with pytest.raises(TypeError, match="must be callable"):
        registry.register("bad_tool", "not a function")  # type: ignore

    with pytest.raises(TypeError, match="must be callable"):
        registry.register("bad_tool", 42)  # type: ignore

    with pytest.raises(TypeError, match="must be callable"):
        registry.register("bad_tool", {"dict": "not callable"})  # type: ignore


def test_register_rejects_empty_name():
    """Test that empty tool names are rejected."""
    registry = ToolRegistry()

    with pytest.raises(ValueError, match="cannot be empty"):
        registry.register("", dummy_sync_tool)

    with pytest.raises(ValueError, match="cannot be empty"):
        registry.register("   ", dummy_sync_tool)


def test_register_rejects_non_string_name():
    """Test that non-string tool names are rejected."""
    registry = ToolRegistry()

    with pytest.raises(TypeError, match="must be a string"):
        registry.register(None, dummy_sync_tool)  # type: ignore

    with pytest.raises(TypeError, match="must be a string"):
        registry.register(123, dummy_sync_tool)  # type: ignore


def test_get_error_includes_available_tools():
    """Test that missing tool error lists available tools."""
    registry = ToolRegistry()
    registry.register("search", dummy_sync_tool)
    registry.register("fetch", dummy_async_tool)

    try:
        registry.get("missing")
        pytest.fail("Should raise KeyError")
    except KeyError as e:
        error_msg = str(e)
        assert "search" in error_msg
        assert "fetch" in error_msg
        assert "Available tools" in error_msg
