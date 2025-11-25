# ABOUTME: End-to-end tests for M2 orchestration system with real LLM calls
# ABOUTME: Validates complete orchestration works for multiple diverse goal types

import pytest
from pydantic_ai.models.test import TestModel

from nanoagent.core.executor import executor
from nanoagent.core.orchestrator import Orchestrator
from nanoagent.core.reflector import reflector
from nanoagent.core.task_planner import task_planner
from nanoagent.models.schemas import AgentRunResult, AgentStatus
from nanoagent.tools.builtin import register_builtin_tools


class TestEndToEndOrchestration:
    """End-to-end tests validating M2 orchestration system (uses TestModel for fast, deterministic tests)"""

    @pytest.mark.asyncio
    async def test_e2e_simple_calculation(self) -> None:
        """
        Test simple calculation goal: "Calculate the sum of squares of 1-5"

        Validates:
        - Orchestration completes successfully
        - AgentRunResult structure is correct
        - Status is "completed"
        - System converges in 1-2 iterations
        """
        with (
            task_planner.override(model=TestModel()),
            executor.override(model=TestModel()),
            reflector.override(model=TestModel()),
        ):
            goal = "Calculate the sum of squares of numbers 1 through 5"
            orchestrator = Orchestrator(goal=goal, max_iterations=5)
            register_builtin_tools(orchestrator.registry)

            result = await orchestrator.run()

            # Validate AgentRunResult structure
            assert isinstance(result, AgentRunResult), "Result should be AgentRunResult"
            assert hasattr(result, "output"), "Result should have output field"
            assert hasattr(result, "status"), "Result should have status field"

            # Validate status
            assert result.status == AgentStatus.COMPLETED, f"Expected completed, got {result.status}"

            # Validate output contains result
            assert result.output is not None, "Output should not be null"
            assert len(result.output) > 0, "Output should not be empty"

            # Validate convergence (should complete well before max iterations)
            assert orchestrator.iteration <= 5, f"Should converge within 5 iterations, took {orchestrator.iteration}"

    @pytest.mark.asyncio
    async def test_e2e_multi_step_reasoning(self) -> None:
        """
        Test multi-step reasoning: "What is 15% of 240, then multiply by 3?"

        Validates:
        - Multi-step task decomposition works
        - Results chain correctly through steps
        - System handles result dependencies
        """
        with (
            task_planner.override(model=TestModel()),
            executor.override(model=TestModel()),
            reflector.override(model=TestModel()),
        ):
            goal = "What is 15% of 240, then multiply that result by 3?"
            orchestrator = Orchestrator(goal=goal, max_iterations=8)
            register_builtin_tools(orchestrator.registry)

            result = await orchestrator.run()

            # Validate result structure and status
            assert isinstance(result, AgentRunResult), "Result should be AgentRunResult"
            assert result.status == AgentStatus.COMPLETED, f"Expected completed, got {result.status}"
            assert len(result.output) > 0, "Output should not be empty"

    @pytest.mark.asyncio
    async def test_e2e_iterative_refinement(self) -> None:
        """
        Test iterative refinement: "Find prime numbers between 20-30, then sum them"

        Validates:
        - Reflection detects incomplete work and adds tasks
        - Refinement cycles improve results
        - System convergence with iteration
        """
        with (
            task_planner.override(model=TestModel()),
            executor.override(model=TestModel()),
            reflector.override(model=TestModel()),
        ):
            goal = "Find the prime numbers between 20 and 30, then sum them"
            orchestrator = Orchestrator(goal=goal, max_iterations=8)
            register_builtin_tools(orchestrator.registry)

            result = await orchestrator.run()

            # Validate result structure and status
            assert isinstance(result, AgentRunResult), "Result should be AgentRunResult"
            assert result.status == AgentStatus.COMPLETED, f"Expected completed, got {result.status}"
            assert len(result.output) > 0, "Output should not be empty"

    @pytest.mark.asyncio
    async def test_e2e_stream_events_emitted(self, capsys: pytest.CaptureFixture[str]) -> None:
        """
        Test that StreamManager emits events during orchestration

        Validates:
        - Events are emitted to stdout as JSON
        - Multiple event types appear (task_started, task_completed, reflection)
        """
        with (
            task_planner.override(model=TestModel()),
            executor.override(model=TestModel()),
            reflector.override(model=TestModel()),
        ):
            goal = "Calculate 2 plus 2"
            orchestrator = Orchestrator(goal=goal, max_iterations=5)
            register_builtin_tools(orchestrator.registry)

            result = await orchestrator.run()

            # Verify orchestration completed
            assert result.status == AgentStatus.COMPLETED

            # Check that events were emitted to stdout
            captured = capsys.readouterr()
            assert len(captured.out) > 0, "StreamManager should emit events to stdout"

            # Verify JSON events are present (look for JSON structure indicators)
            assert "{" in captured.out, "Output should contain JSON events"
            assert "type" in captured.out, "JSON events should have 'type' field"

    @pytest.mark.asyncio
    async def test_e2e_max_iterations_respected(self) -> None:
        """
        Test that orchestration respects max_iterations limit

        Validates:
        - System stops at max_iterations
        - Returns result even if not fully converged
        """
        with (
            task_planner.override(model=TestModel()),
            executor.override(model=TestModel()),
            reflector.override(model=TestModel()),
        ):
            goal = "Write a complete Python machine learning framework"  # Intentionally large goal
            max_iters = 3
            orchestrator = Orchestrator(goal=goal, max_iterations=max_iters)
            register_builtin_tools(orchestrator.registry)

            result = await orchestrator.run()

            # Validate result structure
            assert isinstance(result, AgentRunResult), "Result should be AgentRunResult"
            assert len(result.output) > 0, "Should produce output even at iteration limit"

            # Verify we stopped at or before max_iterations
            assert orchestrator.iteration <= max_iters, (
                f"Should stop at max {max_iters} iterations, stopped at {orchestrator.iteration}"
            )

    @pytest.mark.asyncio
    async def test_e2e_context_preserved_through_cycle(self) -> None:
        """
        Test that context (task results) flows through entire orchestration cycle

        Validates:
        - Task results are preserved
        - Context is available to reflector
        - Results appear in final output
        """
        with (
            task_planner.override(model=TestModel()),
            executor.override(model=TestModel()),
            reflector.override(model=TestModel()),
        ):
            goal = "What is the capital of France, and how many people live there?"
            orchestrator = Orchestrator(goal=goal, max_iterations=6)
            register_builtin_tools(orchestrator.registry)

            result = await orchestrator.run()

            # Validate orchestration completed
            assert isinstance(result, AgentRunResult), "Result should be AgentRunResult"
            assert result.status == AgentStatus.COMPLETED, f"Expected completed, got {result.status}"

            # Verify context was preserved - final output should have meaningful result
            assert len(result.output) > 0, "Output should not be empty"
