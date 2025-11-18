# ABOUTME: Tests for TaskPlanner agent with real Pydantic AI structured outputs
# ABOUTME: Validates Critical Risk #1: Pydantic AI reliably produces structured outputs

from unittest.mock import patch

import pytest
from pydantic_ai import ModelHTTPError

from nanoagent.models.schemas import TaskPlanOutput


@pytest.mark.usefixtures("require_real_api_key")
class TestTaskPlanner:
    """Test suite for TaskPlanner agent (uses real LLM calls)"""

    @pytest.mark.asyncio
    async def test_simple_goal_returns_structured_output(self) -> None:
        """Simple goal returns TaskPlanOutput with tasks"""
        from nanoagent.core.task_planner import task_planner

        result = await task_planner.run("Build a todo application with Python")  # type: ignore[arg-type]

        data = result.output
        assert isinstance(data, TaskPlanOutput)
        assert isinstance(data.tasks, list)
        assert len(data.tasks) >= 3
        assert len(data.tasks) <= 7
        assert all(isinstance(task, str) for task in data.tasks)
        assert all(len(task) > 0 for task in data.tasks)

    @pytest.mark.asyncio
    async def test_clear_goal_produces_actionable_tasks(self) -> None:
        """Clear goal produces specific, actionable task descriptions"""
        from nanoagent.core.task_planner import task_planner

        result = await task_planner.run("Write a Python function that calculates factorial")  # type: ignore[arg-type]

        data = result.output
        assert isinstance(data, TaskPlanOutput)
        assert 3 <= len(data.tasks) <= 7

        # Verify tasks are actionable (not too generic, not too specific)
        for task in data.tasks:
            assert len(task) > 10  # Long enough to be meaningful
            assert len(task) < 500  # Not excessively long

    @pytest.mark.asyncio
    async def test_ambiguous_goal_may_include_questions(self) -> None:
        """Ambiguous goal may include clarifying questions"""
        from nanoagent.core.task_planner import task_planner

        result = await task_planner.run("Make something cool with AI")  # type: ignore[arg-type]

        data = result.output
        assert isinstance(data, TaskPlanOutput)
        assert isinstance(data.questions, list)

        # Questions are optional, but structure should be present
        if data.questions:
            assert all(isinstance(q, str) for q in data.questions)
            assert all(len(q) > 0 for q in data.questions)

    @pytest.mark.asyncio
    async def test_structured_output_always_matches_schema(self) -> None:
        """Any goal produces output matching TaskPlanOutput schema"""
        from nanoagent.core.task_planner import task_planner

        result = await task_planner.run("Deploy a web application to production")  # type: ignore[arg-type]

        output = result.output
        assert isinstance(output, TaskPlanOutput)

        # Validate schema fields exist and have correct types
        assert hasattr(output, "tasks")
        assert hasattr(output, "questions")
        assert isinstance(output.tasks, list)
        assert isinstance(output.questions, list)

        # Validate constraints from schema
        assert len(output.tasks) <= 50  # schema max_length=50
        assert len(output.questions) <= 20  # schema max_length=20

    @pytest.mark.asyncio
    async def test_multiple_calls_produce_consistent_structure(self) -> None:
        """Multiple LLM calls all produce properly structured outputs"""
        from nanoagent.core.task_planner import task_planner

        goals = [
            "Build a REST API",
            "Write unit tests for a calculator",
            "Set up continuous integration",
        ]

        for goal in goals:
            result = await task_planner.run(goal)  # type: ignore[arg-type]

            # Every call must produce valid TaskPlanOutput
            data = result.output
            assert isinstance(data, TaskPlanOutput)
            assert 3 <= len(data.tasks) <= 7
            assert isinstance(data.questions, list)


class TestTaskPlannerErrorHandling:
    """Test suite for TaskPlanner error handling and input validation (no API calls)"""

    @pytest.mark.asyncio
    async def test_empty_goal_raises_value_error(self) -> None:
        """Empty goal string raises ValueError"""
        from nanoagent.core.task_planner import plan_tasks

        with pytest.raises(ValueError, match="cannot be empty"):
            await plan_tasks("")

    @pytest.mark.asyncio
    async def test_whitespace_goal_raises_value_error(self) -> None:
        """Whitespace-only goal raises ValueError"""
        from nanoagent.core.task_planner import plan_tasks

        with pytest.raises(ValueError, match="cannot be empty"):
            await plan_tasks("   ")

        with pytest.raises(ValueError, match="cannot be empty"):
            await plan_tasks("\t\n")

    @pytest.mark.asyncio
    async def test_api_error_returns_none_gracefully(self) -> None:
        """API errors are caught and return None instead of crashing"""
        from nanoagent.core.task_planner import plan_tasks, task_planner

        # Mock the agent to raise ModelHTTPError with proper signature
        error = ModelHTTPError(status_code=429, model_name="anthropic")

        with patch.object(task_planner, "run", side_effect=error):
            result = await plan_tasks("Test goal")
            assert result is None  # Graceful failure, not exception

    @pytest.mark.asyncio
    async def test_network_error_returns_none_gracefully(self) -> None:
        """Network errors are caught and return None instead of crashing"""
        import httpx

        from nanoagent.core.task_planner import plan_tasks, task_planner

        with patch.object(task_planner, "run", side_effect=httpx.ConnectError("Connection failed")):
            result = await plan_tasks("Test goal")
            assert result is None  # Graceful failure

    @pytest.mark.asyncio
    async def test_unexpected_model_behavior_raises_valueerror(self) -> None:
        """UnexpectedModelBehavior is caught, logged, and re-raised as ValueError (Critical Risk #1)"""
        from pydantic_ai import UnexpectedModelBehavior

        from nanoagent.core.task_planner import plan_tasks, task_planner

        error = UnexpectedModelBehavior("Model output doesn't match TaskPlanOutput schema")

        with patch.object(task_planner, "run", side_effect=error):
            with pytest.raises(ValueError, match="Task planning failed.*schema"):
                await plan_tasks("Test goal")

    @pytest.mark.asyncio
    async def test_valid_goal_returns_structured_output(self) -> None:
        """Valid goal with error handling wrapper returns TaskPlanOutput"""
        from pydantic_ai.models.test import TestModel

        # Use TestModel to avoid API calls
        from nanoagent.core.task_planner import plan_tasks, task_planner

        with task_planner.override(model=TestModel()):
            result = await plan_tasks("Build a web application")

            # Should return valid TaskPlanOutput
            assert result is not None
            assert isinstance(result, TaskPlanOutput)
            assert isinstance(result.tasks, list)
            assert isinstance(result.questions, list)
            assert len(result.tasks) > 0

    @pytest.mark.asyncio
    async def test_long_goal_logs_warning_but_succeeds(self) -> None:
        """Extremely long goals succeed but log warning"""

        from pydantic_ai.models.test import TestModel

        from nanoagent.core.task_planner import plan_tasks, task_planner

        # Use TestModel to avoid API calls
        long_goal = "Build " + ("a " * 600) + "application"  # ~3600 chars

        with task_planner.override(model=TestModel()):
            with patch("nanoagent.core.task_planner.logger") as mock_logger:
                result = await plan_tasks(long_goal)

                # Should succeed
                assert result is not None
                # Should log warning about length
                mock_logger.warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_schema_constraints_enforced_on_output(self) -> None:
        """TaskPlanOutput schema constraints (max 50 tasks, 20 questions) are enforced"""
        from pydantic_ai.models.test import TestModel

        from nanoagent.core.task_planner import plan_tasks, task_planner

        with task_planner.override(model=TestModel()):
            result = await plan_tasks("Build enterprise SaaS platform")

            # Schema should enforce constraints from Pydantic model
            assert result is not None
            assert len(result.tasks) <= 50  # Schema max_length constraint
            assert len(result.questions) <= 20  # Schema max_length constraint
            # TestModel generates minimal valid data (at least 1 task)
            assert len(result.tasks) >= 1
            assert len(result.tasks) <= 50  # Respect schema max constraint
            assert isinstance(result.tasks[0], str)  # Tasks are strings
            assert isinstance(result.questions, list)  # Questions is a list

    @pytest.mark.asyncio
    async def test_unexpected_exceptions_are_reraised(self) -> None:
        """Unexpected exceptions are logged but then re-raised (not swallowed)"""
        from nanoagent.core.task_planner import plan_tasks, task_planner

        # Simulate a programming error (not a known exception type)
        error = RuntimeError("Unexpected programming error")

        with patch.object(task_planner, "run", side_effect=error):
            with pytest.raises(RuntimeError, match="Unexpected programming error"):
                await plan_tasks("Test goal")
            # Should NOT return None - should crash

    @pytest.mark.asyncio
    async def test_timeout_error_returns_none_gracefully(self) -> None:
        """Timeout errors are caught and return None instead of crashing"""
        import httpx

        from nanoagent.core.task_planner import plan_tasks, task_planner

        with patch.object(task_planner, "run", side_effect=httpx.TimeoutException("Request timed out")):
            result = await plan_tasks("Test goal")
            assert result is None  # Graceful failure
