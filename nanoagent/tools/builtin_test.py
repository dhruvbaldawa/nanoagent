"""
ABOUTME: Tests for built-in tools (calculator, echo, get_timestamp)
ABOUTME: Validates simple async tool implementations and registry integration
"""

from datetime import datetime

import pytest

from nanoagent.tools.builtin import echo, get_timestamp, mock_calculator, register_builtin_tools
from nanoagent.tools.registry import ToolRegistry


class TestMockCalculator:
    """Tests for mock_calculator tool."""

    @pytest.mark.asyncio
    async def test_simple_addition(self) -> None:
        """Test basic addition."""
        result = await mock_calculator("2 + 3")
        assert "5" in result

    @pytest.mark.asyncio
    async def test_multiplication(self) -> None:
        """Test multiplication."""
        result = await mock_calculator("4 * 5")
        assert "20" in result

    @pytest.mark.asyncio
    async def test_division(self) -> None:
        """Test division."""
        result = await mock_calculator("10 / 2")
        assert "5" in result

    @pytest.mark.asyncio
    async def test_complex_expression(self) -> None:
        """Test complex mathematical expression."""
        result = await mock_calculator("(2 + 3) * 4 - 1")
        assert "19" in result

    @pytest.mark.asyncio
    async def test_power_operation(self) -> None:
        """Test exponentiation."""
        result = await mock_calculator("2 ** 3")
        assert "8" in result

    @pytest.mark.asyncio
    async def test_invalid_expression(self) -> None:
        """Test error handling for invalid expression."""
        result = await mock_calculator("2 + + 3 invalid")
        assert "Error" in result or "error" in result.lower()

    @pytest.mark.asyncio
    async def test_empty_expression(self) -> None:
        """Test error handling for empty input."""
        result = await mock_calculator("")
        assert "Error" in result or "error" in result.lower()

    @pytest.mark.asyncio
    async def test_division_by_zero(self) -> None:
        """Test error handling for division by zero."""
        result = await mock_calculator("1 / 0")
        assert "Error" in result or "error" in result.lower()

    @pytest.mark.asyncio
    async def test_float_division_result(self) -> None:
        """Test that division with non-integer result returns correct float."""
        result = await mock_calculator("5 / 2")
        assert "2.5" in result

    @pytest.mark.asyncio
    async def test_expression_with_whitespace(self) -> None:
        """Test that expressions with extra whitespace are handled correctly."""
        result = await mock_calculator("  2 + 3  ")
        assert "5" in result

    @pytest.mark.asyncio
    async def test_code_injection_import_rejected(self) -> None:
        """Test that code injection attempts are rejected."""
        result = await mock_calculator("__import__('os').system('id')")
        assert "Error" in result or "Unsupported" in result

    @pytest.mark.asyncio
    async def test_code_injection_attribute_rejected(self) -> None:
        """Test that attribute access attempts are rejected."""
        result = await mock_calculator("().__class__.__bases__")
        assert "Error" in result or "Unsupported" in result


class TestEcho:
    """Tests for echo tool."""

    @pytest.mark.asyncio
    async def test_simple_echo(self) -> None:
        """Test basic echo functionality."""
        result = await echo("hello")
        assert result == "hello"

    @pytest.mark.asyncio
    async def test_echo_with_spaces(self) -> None:
        """Test echo with spaces."""
        result = await echo("hello world")
        assert result == "hello world"

    @pytest.mark.asyncio
    async def test_echo_with_special_chars(self) -> None:
        """Test echo with special characters."""
        result = await echo("!@#$%^&*()")
        assert result == "!@#$%^&*()"

    @pytest.mark.asyncio
    async def test_echo_empty_string(self) -> None:
        """Test echo with empty string."""
        result = await echo("")
        assert result == ""

    @pytest.mark.asyncio
    async def test_echo_with_newlines(self) -> None:
        """Test echo with newlines."""
        result = await echo("line1\nline2")
        assert result == "line1\nline2"


class TestGetTimestamp:
    """Tests for get_timestamp tool."""

    @pytest.mark.asyncio
    async def test_timestamp_format(self) -> None:
        """Test that timestamp is in ISO format."""
        result = await get_timestamp()
        # Should be parseable as ISO format
        try:
            datetime.fromisoformat(result)
            is_valid = True
        except ValueError:
            is_valid = False
        assert is_valid

    @pytest.mark.asyncio
    async def test_timestamp_not_empty(self) -> None:
        """Test that timestamp is not empty."""
        result = await get_timestamp()
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_timestamp_contains_date(self) -> None:
        """Test that timestamp contains date components."""
        result = await get_timestamp()
        assert "-" in result  # ISO format has dashes for date


class TestRegisterBuiltinTools:
    """Tests for register_builtin_tools function."""

    def test_register_all_tools(self) -> None:
        """Test that all tools are registered."""
        registry = ToolRegistry()
        register_builtin_tools(registry)

        names = registry.list_names()
        assert "mock_calculator" in names
        assert "echo" in names
        assert "get_timestamp" in names

    def test_registered_tools_are_callable(self) -> None:
        """Test that registered tools are callable."""
        registry = ToolRegistry()
        register_builtin_tools(registry)

        calculator = registry.get("mock_calculator")
        echo_tool = registry.get("echo")
        timestamp = registry.get("get_timestamp")

        assert callable(calculator)
        assert callable(echo_tool)
        assert callable(timestamp)

    @pytest.mark.asyncio
    async def test_tools_work_through_registry(self) -> None:
        """Test that tools can be executed through registry."""
        registry = ToolRegistry()
        register_builtin_tools(registry)

        # Get and run tools through registry
        calculator = registry.get("mock_calculator")
        result = await calculator("2 + 2")
        assert "4" in result

        echo_tool = registry.get("echo")
        result = await echo_tool("test")
        assert result == "test"

        timestamp = registry.get("get_timestamp")
        result = await timestamp()
        assert len(result) > 0
