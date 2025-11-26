# ABOUTME: Tests for automated orchestrator that coordinates planning, execution, and reflection
# ABOUTME: Validates loop termination, iteration limits, and context preservation

from unittest.mock import AsyncMock, patch

import pytest

from nanoagent.core.orchestrator import Orchestrator
from nanoagent.models.schemas import AgentRunResult, AgentStatus, ExecutionResult, ReflectionOutput, TaskPlanOutput
from nanoagent.tools.registry import ToolRegistry


class TestOrchestrator:
    """Tests for Orchestrator automated loop coordination"""

    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self) -> None:
        """Test Orchestrator initializes with required components"""
        goal = "Test goal"
        orchestrator = Orchestrator(goal=goal, max_iterations=5)

        assert orchestrator.goal == goal
        assert orchestrator.max_iterations == 5
        assert orchestrator.iteration == 0
        assert isinstance(orchestrator.context, dict)
        assert len(orchestrator.context) == 0

    @pytest.mark.asyncio
    async def test_orchestrator_with_custom_registry(self) -> None:
        """Test orchestrator can be initialized with custom tool registry"""
        goal = "Test with tools"
        registry = ToolRegistry()
        orchestrator = Orchestrator(goal=goal, max_iterations=5, registry=registry)

        assert orchestrator.registry is registry

    @pytest.mark.asyncio
    async def test_orchestrator_error_handling(self) -> None:
        """Test orchestrator handles errors gracefully"""
        # Empty goal should raise ValueError
        with pytest.raises(ValueError):
            Orchestrator(goal="", max_iterations=5)

        # Negative iterations should raise ValueError
        with pytest.raises(ValueError):
            Orchestrator(goal="Valid goal", max_iterations=-1)

    @pytest.mark.asyncio
    async def test_orchestrator_successful_completion_with_done_reflection(self) -> None:
        """Test orchestrator completes when reflection.done=True"""
        goal = "Write a function"
        orchestrator = Orchestrator(goal=goal, max_iterations=10)

        # Mock plan_tasks to return one task
        mock_plan_output = TaskPlanOutput(tasks=["Task 1"])

        # Mock execute_task to return success
        mock_exec_result = ExecutionResult(success=True, output="Task 1 completed")

        # Mock reflect_on_progress to return done=True (completes on first reflection)
        mock_reflection = ReflectionOutput(
            done=True,
            gaps=[],
            new_tasks=[],
            complete_ids=[],
        )

        with (
            patch("nanoagent.core.orchestrator.plan_tasks", new_callable=AsyncMock) as mock_plan,
            patch("nanoagent.core.orchestrator.execute_task", new_callable=AsyncMock) as mock_exec,
            patch("nanoagent.core.orchestrator.reflect_on_progress", new_callable=AsyncMock) as mock_reflect,
        ):
            mock_plan.return_value = mock_plan_output
            mock_exec.return_value = mock_exec_result
            mock_reflect.return_value = mock_reflection

            result = await orchestrator.run()

            assert isinstance(result, AgentRunResult)
            assert result.status == AgentStatus.COMPLETED
            assert isinstance(result.output, str)
            assert len(result.output) > 0
            # Should have executed at least once
            assert orchestrator.iteration >= 1

    @pytest.mark.asyncio
    async def test_orchestrator_max_iterations_termination(self) -> None:
        """Test orchestrator terminates when max_iterations reached"""
        goal = "Long task"
        max_iters = 2
        orchestrator = Orchestrator(goal=goal, max_iterations=max_iters)

        # Mock plan_tasks
        mock_plan_output = TaskPlanOutput(tasks=["Task 1", "Task 2", "Task 3"])

        # Mock execute_task
        mock_exec_result = ExecutionResult(success=True, output="Task completed")

        # Mock reflect_on_progress to never return done=True (forces max iterations)
        mock_reflection = ReflectionOutput(
            done=False,
            gaps=["Still more work"],
            new_tasks=["Task 4"],
            complete_ids=[],
        )

        with (
            patch("nanoagent.core.orchestrator.plan_tasks", new_callable=AsyncMock) as mock_plan,
            patch("nanoagent.core.orchestrator.execute_task", new_callable=AsyncMock) as mock_exec,
            patch("nanoagent.core.orchestrator.reflect_on_progress", new_callable=AsyncMock) as mock_reflect,
        ):
            mock_plan.return_value = mock_plan_output
            mock_exec.return_value = mock_exec_result
            mock_reflect.return_value = mock_reflection

            result = await orchestrator.run()

            # Should terminate due to iteration limit
            assert isinstance(result, AgentRunResult)
            assert orchestrator.iteration <= orchestrator.max_iterations

    @pytest.mark.asyncio
    async def test_orchestrator_context_preservation(self) -> None:
        """Test orchestrator preserves context through iterations"""
        goal = "Multi-task goal"
        orchestrator = Orchestrator(goal=goal, max_iterations=5)

        # Mock plan_tasks
        mock_plan_output = TaskPlanOutput(tasks=["Task A", "Task B"])

        # Mock execute_task with different outputs per call
        exec_results = [
            ExecutionResult(success=True, output="Result A"),
            ExecutionResult(success=True, output="Result B"),
        ]

        # Mock reflect_on_progress
        mock_reflection = ReflectionOutput(
            done=False,
            gaps=[],
            new_tasks=[],
            complete_ids=[],
        )

        with (
            patch("nanoagent.core.orchestrator.plan_tasks", new_callable=AsyncMock) as mock_plan,
            patch("nanoagent.core.orchestrator.execute_task", new_callable=AsyncMock) as mock_exec,
            patch("nanoagent.core.orchestrator.reflect_on_progress", new_callable=AsyncMock) as mock_reflect,
        ):
            mock_plan.return_value = mock_plan_output
            mock_exec.side_effect = exec_results
            mock_reflect.return_value = mock_reflection

            result = await orchestrator.run()

            # Context should be populated with task results
            assert isinstance(orchestrator.context, dict)
            assert isinstance(result, AgentRunResult)

    @pytest.mark.asyncio
    async def test_orchestrator_reflection_frequency(self) -> None:
        """Test orchestrator triggers reflection periodically"""
        goal = "Task with reflections"
        orchestrator = Orchestrator(goal=goal, max_iterations=10)

        mock_plan_output = TaskPlanOutput(tasks=["T1", "T2", "T3", "T4"])
        mock_exec_result = ExecutionResult(success=True, output="Done")
        mock_reflection = ReflectionOutput(done=False, gaps=[], new_tasks=[], complete_ids=[])

        with (
            patch("nanoagent.core.orchestrator.plan_tasks", new_callable=AsyncMock) as mock_plan,
            patch("nanoagent.core.orchestrator.execute_task", new_callable=AsyncMock) as mock_exec,
            patch("nanoagent.core.orchestrator.reflect_on_progress", new_callable=AsyncMock) as mock_reflect,
        ):
            mock_plan.return_value = mock_plan_output
            mock_exec.return_value = mock_exec_result
            mock_reflect.return_value = mock_reflection

            result = await orchestrator.run()

            # Reflection should be called periodically (at least once)
            assert mock_reflect.called
            assert isinstance(result, AgentRunResult)
            assert orchestrator.iteration >= 1

    @pytest.mark.asyncio
    async def test_orchestrator_iteration_increment(self) -> None:
        """Test orchestrator increments iteration counter"""
        goal = "Simple task"
        orchestrator = Orchestrator(goal=goal, max_iterations=3)

        mock_plan_output = TaskPlanOutput(tasks=["Task 1"])
        mock_exec_result = ExecutionResult(success=True, output="Done")
        mock_reflection = ReflectionOutput(done=True, gaps=[], new_tasks=[], complete_ids=[])

        with (
            patch("nanoagent.core.orchestrator.plan_tasks", new_callable=AsyncMock) as mock_plan,
            patch("nanoagent.core.orchestrator.execute_task", new_callable=AsyncMock) as mock_exec,
            patch("nanoagent.core.orchestrator.reflect_on_progress", new_callable=AsyncMock) as mock_reflect,
        ):
            mock_plan.return_value = mock_plan_output
            mock_exec.return_value = mock_exec_result
            mock_reflect.return_value = mock_reflection

            initial_iteration = orchestrator.iteration
            await orchestrator.run()

            # Iteration should have incremented
            assert orchestrator.iteration > initial_iteration

    @pytest.mark.asyncio
    async def test_reflect_on_progress_returns_none(self) -> None:
        """Test orchestrator handles None return from reflection gracefully"""
        goal = "Test goal"
        orchestrator = Orchestrator(goal=goal, max_iterations=5)

        mock_plan_output = TaskPlanOutput(tasks=["Task 1"])
        mock_exec_result = ExecutionResult(success=True, output="Done")

        with (
            patch("nanoagent.core.orchestrator.plan_tasks", new_callable=AsyncMock) as mock_plan,
            patch("nanoagent.core.orchestrator.execute_task", new_callable=AsyncMock) as mock_exec,
            patch("nanoagent.core.orchestrator.reflect_on_progress", new_callable=AsyncMock) as mock_reflect,
        ):
            mock_plan.return_value = mock_plan_output
            mock_exec.return_value = mock_exec_result
            mock_reflect.return_value = None  # Simulate API failure

            result = await orchestrator.run()

            # Should handle gracefully and return failed status
            assert result.status == AgentStatus.FAILED
            assert "reflection" in result.output.lower()

    @pytest.mark.asyncio
    async def test_failed_execution_not_marked_done(self) -> None:
        """Test that tasks with success=False are not marked as complete"""
        goal = "Test goal"
        orchestrator = Orchestrator(goal=goal, max_iterations=5)

        mock_plan_output = TaskPlanOutput(tasks=["Task 1"])
        mock_exec_result = ExecutionResult(success=False, output="Task failed: permission denied")
        mock_reflection = ReflectionOutput(done=False, gaps=["Task 1 failed"], new_tasks=[], complete_ids=[])

        with (
            patch("nanoagent.core.orchestrator.plan_tasks", new_callable=AsyncMock) as mock_plan,
            patch("nanoagent.core.orchestrator.execute_task", new_callable=AsyncMock) as mock_exec,
            patch("nanoagent.core.orchestrator.reflect_on_progress", new_callable=AsyncMock) as mock_reflect,
        ):
            mock_plan.return_value = mock_plan_output
            mock_exec.return_value = mock_exec_result
            mock_reflect.return_value = mock_reflection

            await orchestrator.run()

            # Failed tasks should NOT be in done list
            done_tasks = orchestrator.todo.get_done()
            assert len(done_tasks) == 0, "Failed tasks should not be marked as done"

    @pytest.mark.asyncio
    async def test_plan_tasks_raises_error(self) -> None:
        """Test orchestrator properly propagates exceptions from planning"""
        goal = "Test goal"
        orchestrator = Orchestrator(goal=goal, max_iterations=5)

        with patch("nanoagent.core.orchestrator.plan_tasks", new_callable=AsyncMock) as mock_plan:
            mock_plan.side_effect = RuntimeError("API error during planning")

            with pytest.raises(RuntimeError, match="API error during planning"):
                await orchestrator.run()

    @pytest.mark.asyncio
    async def test_execute_task_raises_error(self) -> None:
        """Test orchestrator properly propagates exceptions from execution"""
        goal = "Test goal"
        orchestrator = Orchestrator(goal=goal, max_iterations=5)

        mock_plan_output = TaskPlanOutput(tasks=["Task 1"])

        with (
            patch("nanoagent.core.orchestrator.plan_tasks", new_callable=AsyncMock) as mock_plan,
            patch("nanoagent.core.orchestrator.execute_task", new_callable=AsyncMock) as mock_exec,
        ):
            mock_plan.return_value = mock_plan_output
            mock_exec.side_effect = RuntimeError("Task execution timeout")

            with pytest.raises(RuntimeError, match="Task execution timeout"):
                await orchestrator.run()

    @pytest.mark.asyncio
    async def test_reflection_raises_error(self) -> None:
        """Test orchestrator properly propagates exceptions from reflection"""
        goal = "Test goal"
        orchestrator = Orchestrator(goal=goal, max_iterations=5)

        mock_plan_output = TaskPlanOutput(tasks=["Task 1"])
        mock_exec_result = ExecutionResult(success=True, output="Done")

        with (
            patch("nanoagent.core.orchestrator.plan_tasks", new_callable=AsyncMock) as mock_plan,
            patch("nanoagent.core.orchestrator.execute_task", new_callable=AsyncMock) as mock_exec,
            patch("nanoagent.core.orchestrator.reflect_on_progress", new_callable=AsyncMock) as mock_reflect,
        ):
            mock_plan.return_value = mock_plan_output
            mock_exec.return_value = mock_exec_result
            mock_reflect.side_effect = ValueError("Invalid reflection output")

            with pytest.raises(ValueError, match="Invalid reflection"):
                await orchestrator.run()

    @pytest.mark.asyncio
    async def test_empty_initial_task_plan(self) -> None:
        """Test orchestrator handles empty task list from planner"""
        goal = "Unclear goal"
        orchestrator = Orchestrator(goal=goal, max_iterations=5)

        mock_plan_output = TaskPlanOutput(tasks=[])
        # Reflection that marks goal as complete even with no work done
        mock_reflection = ReflectionOutput(
            done=True,
            gaps=[],
            new_tasks=[],
            complete_ids=[],
        )

        with (
            patch("nanoagent.core.orchestrator.plan_tasks", new_callable=AsyncMock) as mock_plan,
            patch("nanoagent.core.orchestrator.reflect_on_progress", new_callable=AsyncMock) as mock_reflect,
        ):
            mock_plan.return_value = mock_plan_output
            mock_reflect.return_value = mock_reflection

            result = await orchestrator.run()

            # Should have reflected immediately with empty plan
            assert mock_reflect.called
            # Should complete since reflection returns done=True
            assert result.status == AgentStatus.COMPLETED

    def test_orchestrator_rejects_whitespace_only_goal(self) -> None:
        """Test that whitespace-only goals are rejected"""
        with pytest.raises(ValueError, match="Goal cannot be empty"):
            Orchestrator(goal="   ", max_iterations=5)

        with pytest.raises(ValueError, match="Goal cannot be empty"):
            Orchestrator(goal="\t\n", max_iterations=5)

    def test_task_description_validation_rejects_shell_commands(self) -> None:
        """Test that validation method rejects shell commands and dangerous patterns"""
        orchestrator = Orchestrator(goal="Test goal", max_iterations=5)

        # Test various dangerous patterns
        dangerous_commands = [
            "Execute: rm -rf /",
            "Run: $(dangerous_code)",
            "eval('malicious')",
            "exec(bad_code)",
            "Use shell: cmd1 | cmd2 & cmd3",
            "System: command && another_command",
        ]

        for cmd in dangerous_commands:
            assert not orchestrator.validate_task_description(cmd), f"Should reject dangerous task: {cmd}"

        # Test that legitimate tasks pass
        legitimate_tasks = [
            "Calculate the sum of numbers 1 through 10",
            "Find prime numbers between 20 and 30",
            "Format user data for display",
        ]

        for task in legitimate_tasks:
            assert orchestrator.validate_task_description(task), f"Should accept legitimate task: {task}"

    @pytest.mark.asyncio
    async def test_context_preserves_correct_task_mappings(self) -> None:
        """Test that context[task_id] contains correct execution result"""
        goal = "Multi-task goal"
        orchestrator = Orchestrator(goal=goal, max_iterations=10)

        mock_plan_output = TaskPlanOutput(tasks=["Task A", "Task B"])
        exec_results = [
            ExecutionResult(success=True, output="Result A"),
            ExecutionResult(success=True, output="Result B"),
        ]
        mock_reflection = ReflectionOutput(done=False, gaps=[], new_tasks=[], complete_ids=[])

        with (
            patch("nanoagent.core.orchestrator.plan_tasks", new_callable=AsyncMock) as mock_plan,
            patch("nanoagent.core.orchestrator.execute_task", new_callable=AsyncMock) as mock_exec,
            patch("nanoagent.core.orchestrator.reflect_on_progress", new_callable=AsyncMock) as mock_reflect,
        ):
            mock_plan.return_value = mock_plan_output
            mock_exec.side_effect = exec_results
            mock_reflect.return_value = mock_reflection

            await orchestrator.run()

            # Verify context has correct mappings
            done_tasks = orchestrator.todo.get_done()
            assert len(done_tasks) == 2
            for task in done_tasks:
                assert task.id in orchestrator.context, f"Task {task.id} not in context"
                assert orchestrator.context[task.id] == task.result, f"Context mismatch for {task.id}"
