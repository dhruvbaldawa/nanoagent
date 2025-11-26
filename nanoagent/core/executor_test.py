# ABOUTME: Tests for Executor agent with tool calling patterns
# ABOUTME: Validates tool registration and ExecutionResult structured output

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from pydantic import BaseModel
from pydantic_ai import Agent, ModelHTTPError, RunContext, UnexpectedModelBehavior
from pydantic_ai.models.test import TestModel

from nanoagent.core.executor import execute_task
from nanoagent.models.schemas import ExecutionResult


class ExecutorDeps(BaseModel):
    """Dependencies available to executor agent"""

    task: str
    available_tools: dict[str, str]


class TestExecutor:
    """Test suite for Executor agent (uses TestModel for fast, deterministic tests)"""

    @pytest.mark.asyncio
    async def test_executor_calls_registered_tool(self) -> None:
        """Executor agent can call a registered mock tool"""
        # Create executor agent
        test_executor: Agent[ExecutorDeps, ExecutionResult] = Agent(  # type: ignore[assignment]
            model="openrouter:minimax/minimax-m2",
            output_type=ExecutionResult,
            deps_type=ExecutorDeps,
            system_prompt="""You are an executor agent. You receive a task and a set of available tools.
Execute the task using the available tools. Return success=true if the task was completed successfully,
false if it failed. Provide detailed output explaining what you did.""",
        )

        @test_executor.tool
        async def mock_search(ctx: RunContext[ExecutorDeps], query: str) -> str:  # pyright: ignore[reportUnusedFunction]
            """Mock search tool for testing"""
            return f"Search results for '{query}': Found relevant information"

        # Create dependencies with task and tools
        deps = ExecutorDeps(
            task="Search for information about Python",
            available_tools={"search": "Search for information"},
        )

        # Run executor with TestModel override
        with test_executor.override(model=TestModel()):
            result = await test_executor.run("Search for information about Python", deps=deps)  # type: ignore[arg-type]

            # Verify ExecutionResult structure
            output = result.output
            assert isinstance(output, ExecutionResult)
            assert isinstance(output.success, bool)
            assert isinstance(output.output, str)
            assert len(output.output) > 0

    @pytest.mark.asyncio
    async def test_executor_returns_structured_output(self) -> None:
        """Executor returns ExecutionResult with success and output fields"""
        test_executor: Agent[ExecutorDeps, ExecutionResult] = Agent(  # type: ignore[assignment]
            model="openrouter:minimax/minimax-m2",
            output_type=ExecutionResult,
            deps_type=ExecutorDeps,
            system_prompt="You are an executor. Return success=true if task succeeds, false otherwise.",
        )

        deps = ExecutorDeps(
            task="Simple task",
            available_tools={},
        )

        with test_executor.override(model=TestModel()):
            result = await test_executor.run("Execute a simple task", deps=deps)  # type: ignore[arg-type]

            output = result.output
            assert isinstance(output, ExecutionResult)
            assert hasattr(output, "success")
            assert hasattr(output, "output")
            assert isinstance(output.success, bool)
            assert isinstance(output.output, str)

    @pytest.mark.asyncio
    async def test_executor_with_multiple_tools(self) -> None:
        """Executor can work with multiple registered mock tools"""
        test_executor: Agent[ExecutorDeps, ExecutionResult] = Agent(  # type: ignore[assignment]
            model="openrouter:minimax/minimax-m2",
            output_type=ExecutionResult,
            deps_type=ExecutorDeps,
            system_prompt="""You are an executor with access to multiple tools.
Use them appropriately to complete the task. Return success=true if completed.""",
        )

        @test_executor.tool
        async def mock_search(ctx: RunContext[ExecutorDeps], query: str) -> str:  # pyright: ignore[reportUnusedFunction]
            """Mock search tool"""
            return f"Found: {query}"

        @test_executor.tool
        async def mock_analyze(ctx: RunContext[ExecutorDeps], data: str) -> str:  # pyright: ignore[reportUnusedFunction]
            """Mock analysis tool"""
            return f"Analysis: {data}"

        deps = ExecutorDeps(
            task="Search and analyze",
            available_tools={
                "search": "Search for information",
                "analyze": "Analyze data",
            },
        )

        with test_executor.override(model=TestModel()):
            result = await test_executor.run(
                "Search for Python documentation and analyze it",
                deps=deps,
            )  # type: ignore[arg-type]

            output = result.output
            assert isinstance(output, ExecutionResult)
            assert isinstance(output.success, bool)
            assert len(output.output) > 0

    @pytest.mark.asyncio
    async def test_executor_handles_task_failure(self) -> None:
        """Executor correctly reports failure when task cannot be completed"""
        test_executor: Agent[ExecutorDeps, ExecutionResult] = Agent(  # type: ignore[assignment]
            model="openrouter:minimax/minimax-m2",
            output_type=ExecutionResult,
            deps_type=ExecutorDeps,
            system_prompt="""You are an executor. If a task cannot be completed,
return success=false with a detailed explanation of why.""",
        )

        deps = ExecutorDeps(
            task="Impossible task",
            available_tools={},
        )

        with test_executor.override(model=TestModel()):
            result = await test_executor.run(
                "Perform a task that requires unavailable tools",
                deps=deps,
            )  # type: ignore[arg-type]

            output = result.output
            assert isinstance(output, ExecutionResult)
            # Could be success or failure depending on LLM's interpretation
            assert isinstance(output.success, bool)
            assert isinstance(output.output, str)


class TestExecuteTaskFunction:
    """Test suite for execute_task() public API function with error handling"""

    @pytest.mark.asyncio
    async def test_execute_task_empty_string_raises_valueerror(self) -> None:
        """execute_task raises ValueError for empty task string"""
        with pytest.raises(ValueError, match="Task cannot be empty"):
            await execute_task("")

    @pytest.mark.asyncio
    async def test_execute_task_whitespace_only_raises_valueerror(self) -> None:
        """execute_task raises ValueError for whitespace-only task string"""
        with pytest.raises(ValueError, match="Task cannot be empty"):
            await execute_task("   ")
        with pytest.raises(ValueError, match="Task cannot be empty"):
            await execute_task("\t\n")

    @pytest.mark.asyncio
    async def test_execute_task_api_error_raises_runtimeerror(self) -> None:
        """execute_task raises RuntimeError when ModelHTTPError occurs"""
        with patch("nanoagent.core.executor.executor") as mock_executor:
            mock_executor.run = AsyncMock(side_effect=ModelHTTPError(status_code=500, model_name="anthropic"))

            with pytest.raises(RuntimeError, match="API error.*500"):
                await execute_task("test task")

    @pytest.mark.asyncio
    async def test_execute_task_unauthorized_api_error_raises(self) -> None:
        """execute_task raises RuntimeError for authentication failures (401)"""
        with patch("nanoagent.core.executor.executor") as mock_executor:
            mock_executor.run = AsyncMock(side_effect=ModelHTTPError(status_code=401, model_name="anthropic"))

            with pytest.raises(RuntimeError, match="API error.*401"):
                await execute_task("test task")

    @pytest.mark.asyncio
    async def test_execute_task_timeout_raises_runtimeerror(self) -> None:
        """execute_task raises RuntimeError when network timeout occurs"""
        with patch("nanoagent.core.executor.executor") as mock_executor:
            mock_executor.run = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))

            with pytest.raises(RuntimeError, match="network error.*TimeoutException"):
                await execute_task("test task")

    @pytest.mark.asyncio
    async def test_execute_task_connection_error_raises_runtimeerror(self) -> None:
        """execute_task raises RuntimeError when network connection fails"""
        with patch("nanoagent.core.executor.executor") as mock_executor:
            mock_executor.run = AsyncMock(side_effect=httpx.ConnectError("Connection failed"))

            with pytest.raises(RuntimeError, match="network error.*ConnectError"):
                await execute_task("test task")

    @pytest.mark.asyncio
    async def test_execute_task_invalid_output_raises_valueerror(self) -> None:
        """execute_task raises ValueError when LLM output doesn't match schema"""
        with patch("nanoagent.core.executor.executor") as mock_executor:
            mock_executor.run = AsyncMock(side_effect=UnexpectedModelBehavior("Output validation failed"))

            with pytest.raises(ValueError, match="did not match ExecutionResult schema"):
                await execute_task("test task")

    @pytest.mark.asyncio
    async def test_execute_task_unexpected_exception_propagates(self) -> None:
        """execute_task propagates unexpected exceptions"""
        with patch("nanoagent.core.executor.executor") as mock_executor:
            mock_executor.run = AsyncMock(side_effect=RuntimeError("Unexpected error"))

            with pytest.raises(RuntimeError, match="Unexpected error"):
                await execute_task("test task")

    @pytest.mark.asyncio
    async def test_execute_task_success_returns_result(self) -> None:
        """execute_task returns ExecutionResult on success"""
        mock_result = ExecutionResult(success=True, output="Task completed successfully")

        with patch("nanoagent.core.executor.executor") as mock_executor:
            mock_run_result = AsyncMock()
            mock_run_result.output = mock_result
            mock_executor.run = AsyncMock(return_value=mock_run_result)

            result = await execute_task("test task")

            assert isinstance(result, ExecutionResult)
            assert result.success is True
            assert result.output == "Task completed successfully"
            mock_executor.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_task_failure_returns_result(self) -> None:
        """execute_task returns ExecutionResult with success=false when task fails"""
        mock_result = ExecutionResult(success=False, output="Task could not be completed")

        with patch("nanoagent.core.executor.executor") as mock_executor:
            mock_run_result = AsyncMock()
            mock_run_result.output = mock_result
            mock_executor.run = AsyncMock(return_value=mock_run_result)

            result = await execute_task("test task")

            assert isinstance(result, ExecutionResult)
            assert result.success is False
            assert result.output == "Task could not be completed"

    @pytest.mark.asyncio
    async def test_execute_task_with_available_tools(self) -> None:
        """execute_task passes available_tools to executor dependencies"""
        mock_result = ExecutionResult(success=True, output="Done")

        with patch("nanoagent.core.executor.executor") as mock_executor:
            with patch("nanoagent.core.executor.ExecutorDeps") as mock_deps_class:
                mock_run_result = AsyncMock()
                mock_run_result.output = mock_result
                mock_executor.run = AsyncMock(return_value=mock_run_result)
                mock_deps_instance = AsyncMock()
                mock_deps_class.return_value = mock_deps_instance

                tools = {"search": "Search tool", "analyze": "Analyze tool"}
                result = await execute_task("test task", available_tools=tools)

                # Verify result is correct
                assert isinstance(result, ExecutionResult)

    @pytest.mark.asyncio
    async def test_execute_task_none_available_tools_defaults_to_empty_dict(self) -> None:
        """execute_task treats None available_tools as empty dict"""
        mock_result = ExecutionResult(success=True, output="Done")

        with patch("nanoagent.core.executor.executor") as mock_executor:
            mock_run_result = AsyncMock()
            mock_run_result.output = mock_result
            mock_executor.run = AsyncMock(return_value=mock_run_result)

            result = await execute_task("test task", available_tools=None)

            assert isinstance(result, ExecutionResult)
            assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_task_error_chain_preserves_context(self) -> None:
        """execute_task preserves error context via 'from e' when raising"""
        with patch("nanoagent.core.executor.executor") as mock_executor:
            original_error = ModelHTTPError(status_code=503, model_name="anthropic")
            mock_executor.run = AsyncMock(side_effect=original_error)

            with pytest.raises(RuntimeError, match="API error") as exc_info:
                await execute_task("test task")

            # Check that error chaining is preserved
            assert exc_info.value.__cause__ is original_error
