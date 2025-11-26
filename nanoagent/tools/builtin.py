"""
ABOUTME: Simple built-in tools for M2 testing (mock_calculator, echo, get_timestamp)
ABOUTME: Minimal implementations to validate orchestration system with real-world operations
"""

import ast
import operator
from datetime import datetime
from typing import Any

from nanoagent.tools.registry import ToolRegistry


async def mock_calculator(expression: str) -> str:
    """Evaluate simple mathematical expressions safely.

    Only allows numeric constants and safe binary/unary operations.
    No function calls, attribute access, or imports allowed.

    Args:
        expression: Mathematical expression as a string (e.g., "2 + 3", "4 * 5")

    Returns:
        String with either the result or an error message
    """
    if not expression or not expression.strip():
        return "Error: Empty expression"

    try:
        stripped = expression.strip()
        parsed = ast.parse(stripped, mode="eval")
        result = _safe_eval_ast(parsed.body)
        return f"Result: {result}"
    except ValueError as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Error: Invalid expression - {type(e).__name__}"


def _safe_eval_ast(node: Any) -> float | int:
    """Safely evaluate AST node with only allowed operations.

    Allowed:
    - Numeric constants (int, float)
    - Binary operations: +, -, *, /, //, %, **
    - Unary operations: +, -

    Not allowed: function calls, attribute access, imports, assignments, etc.

    Args:
        node: AST node to evaluate

    Returns:
        Evaluated numeric result

    Raises:
        ValueError: If node type is not allowed
        ZeroDivisionError: If division by zero occurs
    """
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant: {node.value}")
    if isinstance(node, ast.BinOp):
        left = _safe_eval_ast(node.left)
        right = _safe_eval_ast(node.right)
        ops = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.FloorDiv: operator.floordiv,
            ast.Mod: operator.mod,
            ast.Pow: operator.pow,
        }
        op_type = type(node.op)
        if op_type not in ops:
            raise ValueError(f"Unsupported operator: {op_type.__name__}")
        return ops[op_type](left, right)
    if isinstance(node, ast.UnaryOp):
        operand = _safe_eval_ast(node.operand)
        ops = {ast.UAdd: operator.pos, ast.USub: operator.neg}
        op_type = type(node.op)
        if op_type not in ops:
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
        return ops[op_type](operand)
    raise ValueError(f"Unsupported expression: {type(node).__name__}")


async def echo(message: str) -> str:
    """Echo back the input message.

    Args:
        message: Message to echo

    Returns:
        The same message unchanged
    """
    return message


async def get_timestamp() -> str:
    """Get current timestamp in ISO format.

    Returns:
        Current timestamp as ISO format string
    """
    return datetime.now().isoformat()


def register_builtin_tools(registry: ToolRegistry) -> None:
    """Register all built-in tools in the registry.

    Args:
        registry: ToolRegistry instance to register tools in

    Raises:
        TypeError: If registry is invalid or a tool is not callable
        ValueError: If a tool name is invalid
    """
    tools = [
        ("mock_calculator", mock_calculator),
        ("echo", echo),
        ("get_timestamp", get_timestamp),
    ]

    for name, func in tools:
        try:
            registry.register(name, func)
        except (TypeError, ValueError) as e:
            raise type(e)(f"Failed to register tool '{name}': {str(e)}") from e
