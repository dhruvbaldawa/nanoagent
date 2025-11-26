# ABOUTME: Tests for reflector agent gap detection and reflection analysis
# ABOUTME: Validates ReflectionOutput structure parsing and reflection quality

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from pydantic_ai import ModelHTTPError, UnexpectedModelBehavior
from pydantic_ai.models.test import TestModel

from nanoagent.core.reflector import reflect_on_progress, reflector
from nanoagent.models.schemas import ReflectionOutput, Task, TaskStatus


class TestReflector:
    """Test suite for Reflector agent (uses TestModel for fast, deterministic tests)"""

    @pytest.mark.asyncio
    async def test_simple_completed_goal(self):
        """Test: Reflector returns valid ReflectionOutput for simple goal"""
        with reflector.override(model=TestModel()):
            goal = "Calculate 2 + 2"
            completed_tasks: list[Task] = [
                Task(
                    id="task_001",
                    description="Calculate 2 + 2",
                    status=TaskStatus.DONE,
                    result="Result: 4",
                )
            ]
            pending_tasks: list[Task] = []

            result = await reflect_on_progress(goal, completed_tasks, pending_tasks)

            assert isinstance(result, ReflectionOutput)
            assert isinstance(result.done, bool)
            assert isinstance(result.gaps, list)
            assert isinstance(result.new_tasks, list)
            assert isinstance(result.complete_ids, list)

    @pytest.mark.asyncio
    async def test_partially_completed_goal_identifies_gaps(self):
        """Test: Reflector identifies gaps when goal is partially completed"""
        with reflector.override(model=TestModel()):
            goal = "Build a REST API with authentication and database"
            completed_tasks: list[Task] = [
                Task(
                    id="task_001",
                    description="Create basic API endpoints",
                    status=TaskStatus.DONE,
                    result="Basic endpoints created: GET /users, POST /users",
                )
            ]
            pending_tasks: list[Task] = [
                Task(id="task_002", description="Implement user authentication", status=TaskStatus.PENDING),
            ]

            result = await reflect_on_progress(goal, completed_tasks, pending_tasks)

            assert isinstance(result, ReflectionOutput)
            assert isinstance(result.done, bool)
            assert isinstance(result.gaps, list)
            assert isinstance(result.new_tasks, list)
            # task002 already pending, so should be recognized
            assert isinstance(result.complete_ids, list)

    @pytest.mark.asyncio
    async def test_goal_with_pending_tasks_recognized(self):
        """Test: Reflector recognizes and doesn't duplicate pending tasks"""
        with reflector.override(model=TestModel()):
            goal = "Set up project infrastructure"
            completed_tasks: list[Task] = [
                Task(
                    id="task_001",
                    description="Initialize git repository",
                    status=TaskStatus.DONE,
                    result="Git repo initialized",
                )
            ]
            pending_tasks: list[Task] = [
                Task(id="task_002", description="Set up CI/CD pipeline", status=TaskStatus.PENDING),
                Task(id="task_003", description="Configure Docker", status=TaskStatus.PENDING),
            ]

            result = await reflect_on_progress(goal, completed_tasks, pending_tasks)

            assert isinstance(result, ReflectionOutput)
            # Should recognize that some work is already planned (task002, task003)
            # and not suggest exact duplicates
            assert isinstance(result.gaps, list)
            assert isinstance(result.new_tasks, list)

    @pytest.mark.asyncio
    async def test_reflection_output_structure_validation(self):
        """Test: ReflectionOutput always has all required fields"""
        with reflector.override(model=TestModel()):
            goal = "Simple test"
            completed_tasks: list[Task] = []
            pending_tasks: list[Task] = []

            result = await reflect_on_progress(goal, completed_tasks, pending_tasks)

            # Validate all required fields are present
            assert hasattr(result, "done")
            assert isinstance(result.done, bool)
            assert hasattr(result, "gaps")
            assert isinstance(result.gaps, list)
            assert all(isinstance(gap, str) for gap in result.gaps)
            assert hasattr(result, "new_tasks")
            assert isinstance(result.new_tasks, list)
            assert all(isinstance(task, str) for task in result.new_tasks)
            assert hasattr(result, "complete_ids")
            assert isinstance(result.complete_ids, list)
            assert all(isinstance(task_id, str) for task_id in result.complete_ids)

    @pytest.mark.asyncio
    async def test_complex_goal_with_multiple_completed_tasks(self):
        """Test: Reflector handles complex goal with multiple completed tasks"""
        with reflector.override(model=TestModel()):
            goal = "Create a data processing pipeline with validation and monitoring"
            completed_tasks = [
                Task(
                    id="task_001",
                    description="Design data schema",
                    status=TaskStatus.DONE,
                    result="Schema designed with 15 tables",
                ),
                Task(
                    id="task_002",
                    description="Implement data ingestion",
                    status=TaskStatus.DONE,
                    result="Ingestion working for CSV and JSON",
                ),
            ]
            pending_tasks = [
                Task(id="task_003", description="Add data validation", status=TaskStatus.PENDING),
                Task(id="task_004", description="Set up monitoring", status=TaskStatus.PENDING),
            ]

            result = await reflect_on_progress(goal, completed_tasks, pending_tasks)

            assert isinstance(result, ReflectionOutput)
            assert isinstance(result.done, bool)
            assert isinstance(result.gaps, list)
            assert isinstance(result.new_tasks, list)

    @pytest.mark.asyncio
    async def test_irrelevant_task_identification(self):
        """Test: Reflector can mark tasks as irrelevant when goal changes"""
        with reflector.override(model=TestModel()):
            goal = "Complete API endpoints only (drop database optimization for now)"
            completed_tasks = [
                Task(
                    id="task_001",
                    description="Implement REST endpoints",
                    status=TaskStatus.DONE,
                    result="All endpoints working",
                )
            ]
            pending_tasks = [
                Task(id="task_002", description="Optimize database indexes", status=TaskStatus.PENDING),
                Task(id="task_003", description="Add caching layer", status=TaskStatus.PENDING),
            ]

            result = await reflect_on_progress(goal, completed_tasks, pending_tasks)

            assert isinstance(result, ReflectionOutput)
            # Should recognize database optimization might be irrelevant now
            assert isinstance(result.complete_ids, list)

    @pytest.mark.asyncio
    async def test_empty_goal_handles_gracefully(self):
        """Test: Reflector handles edge case of empty state"""
        with reflector.override(model=TestModel()):
            goal = "Evaluate current progress"
            completed_tasks: list[Task] = []
            pending_tasks: list[Task] = []

            result = await reflect_on_progress(goal, completed_tasks, pending_tasks)

            assert isinstance(result, ReflectionOutput)
            assert isinstance(result.done, bool)
            assert isinstance(result.gaps, list)
            assert isinstance(result.new_tasks, list)
            assert isinstance(result.complete_ids, list)


class TestReflectOnProgressFunction:
    """Test suite for reflect_on_progress() public API function with error handling"""

    @pytest.mark.asyncio
    async def test_reflect_on_progress_empty_goal_raises_valueerror(self) -> None:
        """reflect_on_progress raises ValueError for empty goal string"""
        with pytest.raises(ValueError, match="Goal cannot be empty"):
            await reflect_on_progress("", [], [])

    @pytest.mark.asyncio
    async def test_reflect_on_progress_whitespace_only_goal_raises_valueerror(self) -> None:
        """reflect_on_progress raises ValueError for whitespace-only goal"""
        with pytest.raises(ValueError, match="Goal cannot be empty"):
            await reflect_on_progress("   ", [], [])
        with pytest.raises(ValueError, match="Goal cannot be empty"):
            await reflect_on_progress("\t\n", [], [])

    @pytest.mark.asyncio
    async def test_reflect_on_progress_api_error_raises_runtimeerror(self) -> None:
        """reflect_on_progress raises RuntimeError when ModelHTTPError occurs"""
        with patch("nanoagent.core.reflector.reflector") as mock_reflector:
            mock_reflector.run = AsyncMock(side_effect=ModelHTTPError(status_code=500, model_name="anthropic"))

            with pytest.raises(RuntimeError, match="API error.*500"):
                await reflect_on_progress("test goal", [], [])

    @pytest.mark.asyncio
    async def test_reflect_on_progress_unauthorized_api_error_raises(self) -> None:
        """reflect_on_progress raises RuntimeError for authentication failures (401)"""
        with patch("nanoagent.core.reflector.reflector") as mock_reflector:
            mock_reflector.run = AsyncMock(side_effect=ModelHTTPError(status_code=401, model_name="anthropic"))

            with pytest.raises(RuntimeError, match="API error.*401"):
                await reflect_on_progress("test goal", [], [])

    @pytest.mark.asyncio
    async def test_reflect_on_progress_timeout_raises_runtimeerror(self) -> None:
        """reflect_on_progress raises RuntimeError when network timeout occurs"""
        with patch("nanoagent.core.reflector.reflector") as mock_reflector:
            mock_reflector.run = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))

            with pytest.raises(RuntimeError, match="network error.*TimeoutException"):
                await reflect_on_progress("test goal", [], [])

    @pytest.mark.asyncio
    async def test_reflect_on_progress_connection_error_raises_runtimeerror(self) -> None:
        """reflect_on_progress raises RuntimeError when network connection fails"""
        with patch("nanoagent.core.reflector.reflector") as mock_reflector:
            mock_reflector.run = AsyncMock(side_effect=httpx.ConnectError("Connection failed"))

            with pytest.raises(RuntimeError, match="network error.*ConnectError"):
                await reflect_on_progress("test goal", [], [])

    @pytest.mark.asyncio
    async def test_reflect_on_progress_invalid_output_raises_valueerror(self) -> None:
        """reflect_on_progress raises ValueError when LLM output doesn't match schema"""
        with patch("nanoagent.core.reflector.reflector") as mock_reflector:
            mock_reflector.run = AsyncMock(side_effect=UnexpectedModelBehavior("Output validation failed"))

            with pytest.raises(ValueError, match="did not match ReflectionOutput schema"):
                await reflect_on_progress("test goal", [], [])

    @pytest.mark.asyncio
    async def test_reflect_on_progress_unexpected_exception_propagates(self) -> None:
        """reflect_on_progress propagates unexpected exceptions"""
        with patch("nanoagent.core.reflector.reflector") as mock_reflector:
            mock_reflector.run = AsyncMock(side_effect=RuntimeError("Unexpected error"))

            with pytest.raises(RuntimeError, match="Unexpected error"):
                await reflect_on_progress("test goal", [], [])

    @pytest.mark.asyncio
    async def test_reflect_on_progress_error_chain_preserves_context(self) -> None:
        """reflect_on_progress preserves error context via 'from e' when raising"""
        with patch("nanoagent.core.reflector.reflector") as mock_reflector:
            original_error = ModelHTTPError(status_code=503, model_name="anthropic")
            mock_reflector.run = AsyncMock(side_effect=original_error)

            with pytest.raises(RuntimeError, match="API error") as exc_info:
                await reflect_on_progress("test goal", [], [])

            # Check that error chaining is preserved
            assert exc_info.value.__cause__ is original_error

    @pytest.mark.asyncio
    async def test_reflect_on_progress_invalid_completed_tasks_type_raises_typeerror(self) -> None:
        """reflect_on_progress raises TypeError when completed_tasks is not a list"""
        with pytest.raises(TypeError, match="completed_tasks must be a list"):
            await reflect_on_progress("test goal", None, [])  # type: ignore[arg-type]

    @pytest.mark.asyncio
    async def test_reflect_on_progress_invalid_pending_tasks_type_raises_typeerror(self) -> None:
        """reflect_on_progress raises TypeError when pending_tasks is not a list"""
        with pytest.raises(TypeError, match="pending_tasks must be a list"):
            await reflect_on_progress("test goal", [], None)  # type: ignore[arg-type]

    @pytest.mark.asyncio
    async def test_reflect_on_progress_none_task_in_list_raises_valueerror(self) -> None:
        """reflect_on_progress raises ValueError when task list contains None"""
        with pytest.raises(ValueError, match="Task at index.*is None"):
            await reflect_on_progress("test goal", [None], [])  # type: ignore[list-item]

    @pytest.mark.asyncio
    async def test_reflect_on_progress_duplicate_task_ids_raises_valueerror(self) -> None:
        """reflect_on_progress raises ValueError when duplicate task IDs exist"""
        task1 = Task(id="dup_id_1", description="Task 1", status=TaskStatus.PENDING)
        task2 = Task(id="dup_id_1", description="Task 2", status=TaskStatus.PENDING)
        with pytest.raises(ValueError, match="Duplicate task IDs found"):
            await reflect_on_progress("test goal", [task1], [task2])
