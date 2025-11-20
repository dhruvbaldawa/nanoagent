"""
ABOUTME: Simple tool registry for pluggable tool management
ABOUTME: Provides registration, lookup, and listing of callable tools
"""

from collections.abc import Callable
from typing import Any


class ToolRegistry:
    """Registry for managing pluggable tools."""

    def __init__(self) -> None:
        """Initialize empty tool registry."""
        self.tools: dict[str, Callable[..., Any]] = {}

    def register(self, name: str, func: Callable[..., Any] | None) -> None:
        """Register a tool in the registry.

        Args:
            name: Name of the tool (non-empty string)
            func: Callable (sync or async function)

        Raises:
            TypeError: If name is not a string or func is not callable/None
            ValueError: If name is empty or whitespace-only
        """
        if not isinstance(name, str):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError(f"Tool name must be a string, got {type(name).__name__}")
        if not name or not name.strip():
            raise ValueError("Tool name cannot be empty or whitespace-only")
        if func is None:
            raise TypeError(f"Cannot register tool '{name}': func cannot be None")
        if not callable(func):
            raise TypeError(f"Cannot register tool '{name}': func must be callable, got {type(func).__name__}")
        self.tools[name] = func

    def get(self, name: str) -> Callable[..., Any]:
        """Retrieve a tool from the registry.

        Args:
            name: Name of the tool

        Returns:
            The registered callable

        Raises:
            KeyError: If tool is not registered (includes available tools in message)
        """
        if name not in self.tools:
            available = ", ".join(self.list_names()) or "none"
            raise KeyError(f"Tool '{name}' not found. Available tools: {available}")
        return self.tools[name]

    def list_names(self) -> list[str]:
        """Get list of all registered tool names.

        Returns:
            List of tool names
        """
        return list(self.tools.keys())
