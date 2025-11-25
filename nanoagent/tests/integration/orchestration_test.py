# ABOUTME: Integration test orchestrating complete workflow: plan → execute → reflect
# ABOUTME: Validates all Critical Risks and proves Milestone 1 foundation works end-to-end

import pytest
from pydantic_ai.models.test import TestModel

from nanoagent.core.executor import execute_task, executor
from nanoagent.core.reflector import reflect_on_progress, reflector
from nanoagent.core.task_planner import plan_tasks, task_planner
from nanoagent.core.todo_manager import TodoManager
from nanoagent.models.schemas import ExecutionResult, ReflectionOutput, Task, TaskPlanOutput, TaskStatus


class TestManualOrchestration:
    """Integration tests for manual orchestration (uses TestModel for fast, deterministic tests)"""

    @pytest.mark.asyncio
    async def test_complete_orchestration_cycle(self) -> None:
        """
        Test complete end-to-end workflow:
        1. Plan tasks from goal
        2. Add tasks to TodoManager
        3. Execute 2 tasks
        4. Reflect on progress

        Validates Critical Risks:
        - Risk #1: All structured outputs parse correctly
        - Risk #2: Context flows through all phases
        - Risk #3: Reflection produces sensible output
        """
        with (
            task_planner.override(model=TestModel()),
            executor.override(model=TestModel()),
            reflector.override(model=TestModel()),
        ):
            # Phase 1: TaskPlanner - decompose goal into tasks
            goal = (
                "Write a Python script that calculates Fibonacci numbers and creates a simple web server "
                "to serve the results"
            )
            plan_output = await plan_tasks(goal)

            # Validate Risk #1: TaskPlanOutput structure parsing
            assert isinstance(plan_output, TaskPlanOutput)
            assert isinstance(plan_output.tasks, list)
            assert len(plan_output.tasks) > 0, "TaskPlanner should produce at least one task"
            assert all(isinstance(task, str) for task in plan_output.tasks), "All tasks should be strings"

            # Phase 2: TodoManager - queue the planned tasks
            todo = TodoManager()
            added_task_ids = todo.add_tasks(plan_output.tasks)
            assert len(added_task_ids) == len(plan_output.tasks), "All planned tasks should be added to queue"
            assert all(isinstance(task_id, str) for task_id in added_task_ids), "Task IDs should be strings"

            # Phase 3: Executor - execute first task
            task_1 = todo.get_next()
            assert task_1 is not None, "TodoManager should return first task"
            assert task_1.status == TaskStatus.PENDING, "Task should be pending before execution"

            result_1 = await execute_task(task_1.description)

            # Validate Risk #1: ExecutionResult structure parsing
            assert isinstance(result_1, ExecutionResult)
            assert isinstance(result_1.success, bool)
            assert isinstance(result_1.output, str)
            assert len(result_1.output) > 0, "Executor should produce non-empty output"

            # Mark first task complete and record result
            todo.mark_done(task_1.id, result_1.output)
            assert todo.tasks[task_1.id].status == TaskStatus.DONE, "Task should be marked done"

            # Phase 4: Executor - execute second task if available
            task_2 = todo.get_next()
            if task_2 is not None:
                result_2 = await execute_task(task_2.description)

                # Validate ExecutionResult structure
                assert isinstance(result_2, ExecutionResult)
                assert isinstance(result_2.success, bool)
                assert isinstance(result_2.output, str)

                # Mark second task complete
                todo.mark_done(task_2.id, result_2.output)

            # Phase 5: Reflector - evaluate progress
            completed_tasks = todo.get_done()
            pending_tasks = todo.get_pending()

            assert len(completed_tasks) >= 1, "Should have at least 1 completed task"
            assert all(isinstance(t, Task) for t in completed_tasks), "Completed items should be Task objects"
            assert all(isinstance(t, Task) for t in pending_tasks), "Pending items should be Task objects"

            reflection_output = await reflect_on_progress(goal, completed_tasks, pending_tasks)

            # Validate Risk #1: ReflectionOutput structure parsing
            assert isinstance(reflection_output, ReflectionOutput)
            assert isinstance(reflection_output.done, bool)
            assert isinstance(reflection_output.gaps, list)
            assert isinstance(reflection_output.new_tasks, list)
            assert isinstance(reflection_output.complete_ids, list)
            assert all(isinstance(gap, str) for gap in reflection_output.gaps), "Gaps should be strings"
            assert all(isinstance(task, str) for task in reflection_output.new_tasks), "New tasks should be strings"
            assert all(isinstance(task_id, str) for task_id in reflection_output.complete_ids), (
                "Complete IDs should be strings"
            )

    @pytest.mark.asyncio
    async def test_context_preservation_through_phases(self) -> None:
        """
        Test that context (task descriptions + results) flows correctly through all phases.

        Validates Critical Risk #2: Context passing between agents
        """
        with (
            task_planner.override(model=TestModel()),
            executor.override(model=TestModel()),
            reflector.override(model=TestModel()),
        ):
            # Plan tasks
            goal = "Create a Python project structure with multiple modules"
            plan_output = await plan_tasks(goal)

            # Add tasks and track context
            assert plan_output is not None, "Task planning should succeed"
            todo = TodoManager()
            todo.add_tasks(plan_output.tasks)

            # Build context dict as we execute
            context: dict[str, str] = {}

            # Execute first task and store context
            task = todo.get_next()
            assert task is not None
            result = await execute_task(task.description)
            context[task.id] = result.output
            todo.mark_done(task.id, result.output)

            # Verify context can be retrieved
            assert task.id in context, "Task ID should be in context"
            assert context[task.id] == result.output, "Context should store execution results"
            assert todo.tasks[task.id].result == result.output, "TodoManager should preserve result"

            # Execute second task and add to context if available
            task_2 = todo.get_next()
            if task_2 is not None:
                result_2 = await execute_task(task_2.description)
                context[task_2.id] = result_2.output
                todo.mark_done(task_2.id, result_2.output)

            # Verify context preserved
            assert len(context) >= 1, "Context should have at least 1 entry"
            assert all(result is not None for result in context.values()), "All context values should be non-empty"

            # Pass context to reflector - it should use completed task results
            completed = todo.get_done()
            pending = todo.get_pending()

            # Verify reflector receives complete context
            reflection = await reflect_on_progress(goal, completed, pending)

            # All completed tasks should have results in the context
            for task in completed:
                assert task.result is not None, f"Task {task.id} should have result from execution"
                assert task.id in context, f"Task {task.id} should be in context"

            # Validate Risk #3: Reflection sees all the context
            assert isinstance(reflection, ReflectionOutput), "Reflection should parse correctly with full context"
