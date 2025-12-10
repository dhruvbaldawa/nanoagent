# ABOUTME: Automated orchestrator loop that coordinates planning, execution, and reflection
# ABOUTME: Implements planning → execution → reflection cycle with configurable iteration limits

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from nanoagent.core.executor import execute_task
from nanoagent.core.reflector import reflect_on_progress
from nanoagent.core.stream_manager import StreamManager
from nanoagent.core.task_planner import plan_tasks
from nanoagent.core.todo_manager import TodoManager
from nanoagent.models.schemas import AgentRunResult, AgentStatus, ReflectionOutput, TaskStatus
from nanoagent.tools.registry import ToolRegistry

if TYPE_CHECKING:
    from nanoagent.persistence.protocols import ContextStore, RunStore, TaskStore

from nanoagent.persistence.protocols import Phase

logger = logging.getLogger(__name__)

# Reflection frequency: trigger every N iterations
REFLECTION_FREQUENCY = 3


class Orchestrator:
    """
    Orchestrator automates the planning → execution → reflection cycle.

    Coordinates TaskPlanner, Executor, Reflector, and TodoManager to iteratively
    decompose goals, execute tasks, and evaluate progress toward goal completion.
    """

    def __init__(
        self,
        goal: str,
        max_iterations: int = 10,
        registry: ToolRegistry | None = None,
        run_store: RunStore | None = None,
        task_store: TaskStore | None = None,
        context_store: ContextStore | None = None,
        run_id: str | None = None,
    ) -> None:
        """
        Initialize Orchestrator with goal and iteration limits.

        Args:
            goal: High-level goal to accomplish
            max_iterations: Maximum iterations before terminating (must be > 0)
            registry: Optional ToolRegistry for task execution (creates new if not provided)
            run_store: Optional RunStore for run lifecycle persistence
            task_store: Optional TaskStore for task persistence
            context_store: Optional ContextStore for execution context persistence
            run_id: Required when stores provided, unique run identifier

        Raises:
            ValueError: If goal is empty/whitespace-only or max_iterations <= 0
            ValueError: If stores provided without all stores or without run_id
        """
        # Input validation
        if not goal or not goal.strip():
            raise ValueError("Goal cannot be empty or whitespace-only")

        if max_iterations <= 0:
            raise ValueError("max_iterations must be greater than 0")

        # All-or-nothing store validation
        stores = [run_store, task_store, context_store]
        stores_provided = sum(1 for s in stores if s is not None)
        if stores_provided > 0 and stores_provided < 3:
            raise ValueError("If any store is provided, all stores must be provided")

        if stores_provided == 3 and run_id is None:
            raise ValueError("run_id is required when stores are provided")

        self.goal = goal
        self.max_iterations = max_iterations
        self.registry = registry or ToolRegistry()
        self.stream = StreamManager()
        self.context: dict[str, str] = {}
        self.iteration = 0

        # Store references for persistence
        self._run_store = run_store
        self._task_store = task_store
        self._context_store = context_store
        self._run_id = run_id

        # Create TodoManager - with persistence if stores provided
        if task_store is not None and run_id is not None:
            self.todo = TodoManager(store=task_store, run_id=run_id)
        else:
            self.todo = TodoManager()

        # Create run record if stores provided
        if run_store is not None and run_id is not None:
            run_store.create(run_id, goal, max_iterations)

        logger.info(
            "Orchestrator initialized",
            extra={
                "goal": goal[:100],
                "max_iterations": max_iterations,
                "persistent": run_store is not None,
            },
        )

    async def run(self) -> AgentRunResult:
        """
        Execute automated orchestration loop: plan → execute → reflect.

        Returns:
            AgentRunResult with aggregated output and status

        Raises:
            ValueError: If goal is empty/whitespace, max_iterations invalid, or planning produces invalid output
            RuntimeError: If execution or reflection fails with API/network errors
            TypeError: If task lists are malformed or dependency returns invalid types
            Exception: Other unexpected runtime errors during orchestration
        """
        logger.info(
            "Starting orchestration loop",
            extra={"goal": self.goal[:100], "max_iterations": self.max_iterations},
        )

        try:
            # Phase 0: Plan initial tasks
            plan_output = await plan_tasks(self.goal)
            if plan_output is None:
                return AgentRunResult(
                    output="Planning failed: unable to decompose goal",
                    status=AgentStatus.FAILED,
                )

            self.todo.add_tasks(plan_output.tasks)
            logger.info(
                "Tasks planned",
                extra={"task_count": len(plan_output.tasks)},
            )

            # Checkpoint: transition to EXECUTING phase
            if self._run_store is not None and self._run_id is not None:
                self._run_store.update_loop_state(self._run_id, Phase.EXECUTING, 0, None)

            # Phase 1: Execution loop
            while self.iteration < self.max_iterations:
                self.iteration += 1
                result = await self._iteration_step()
                if result is not None:
                    return result

            # Phase 2: Max iterations reached
            logger.info(
                "Max iterations reached",
                extra={
                    "iteration": self.iteration,
                    "completed_tasks": len(self.todo.get_done()),
                },
            )

            # Checkpoint: transition to DONE phase
            if self._run_store is not None and self._run_id is not None:
                self._run_store.update_loop_state(self._run_id, Phase.DONE, self.iteration, None)

            return AgentRunResult(
                output=self._synthesize_result(),
                status=AgentStatus.COMPLETED,
            )

        except (ValueError, RuntimeError) as e:
            logger.error(
                f"{type(e).__name__} during orchestration",
                extra={"error": str(e), "iteration": self.iteration},
                exc_info=True,
            )
            raise

        except Exception as e:
            logger.error(
                "Unexpected error during orchestration",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "iteration": self.iteration,
                },
                exc_info=True,
            )
            raise

    async def _iteration_step(self) -> AgentRunResult | None:
        """
        Execute one iteration: get task, execute, periodically reflect.

        Returns:
            AgentRunResult if orchestration is complete, None to continue
        """
        logger.debug(
            "Iteration started",
            extra={
                "iteration": self.iteration,
                "pending_tasks": len(self.todo.get_pending()),
            },
        )

        current_task = self.todo.get_next()
        if current_task is None:
            return await self._reflect_and_check_completion()

        # Checkpoint: before executing task (with task_id)
        if self._run_store is not None and self._run_id is not None:
            self._run_store.update_loop_state(self._run_id, Phase.EXECUTING, self.iteration, current_task.id)

        # Emit task_started event (fire-and-forget, never raises)
        self.stream.emit("task_started", {"task_id": current_task.id, "description": current_task.description})

        # Execute task
        execution_result = await execute_task(current_task.description)

        # Store context - both in-memory and persistent
        self.context[current_task.id] = execution_result.output
        if self._context_store is not None and self._run_id is not None:
            self._context_store.save_result(self._run_id, current_task.id, execution_result.output)

        # Emit task_completed event (fire-and-forget, never raises)
        self.stream.emit(
            "task_completed",
            {"task_id": current_task.id, "success": execution_result.success, "output": execution_result.output},
        )

        if execution_result.success:
            self.todo.mark_done(current_task.id, execution_result.output)
            logger.debug(
                "Task completed successfully",
                extra={"task_id": current_task.id},
            )
        else:
            logger.warning(
                "Task execution failed",
                extra={
                    "task_id": current_task.id,
                    "output": execution_result.output[:200],
                },
            )

        # Periodic reflection
        if self.iteration % REFLECTION_FREQUENCY == 0:
            return await self._reflect_and_check_completion()

        return None

    async def _reflect_and_check_completion(self) -> AgentRunResult | None:
        """
        Reflect on progress and check if goal is complete.

        Returns:
            AgentRunResult if done, None to continue
        """
        # Checkpoint: transition to REFLECTING phase
        if self._run_store is not None and self._run_id is not None:
            self._run_store.update_loop_state(self._run_id, Phase.REFLECTING, self.iteration, None)

        logger.debug("Reflecting on progress")
        reflection = await reflect_on_progress(self.goal, self.todo.get_done(), self.todo.get_pending())

        # Emit reflection event (fire-and-forget, never raises)
        self.stream.emit(
            "reflection",
            {
                "done": reflection.done if reflection else False,
                "gaps": reflection.gaps if reflection else [],
                "new_tasks": reflection.new_tasks if reflection else [],
            },
        )

        # Handle reflection failure (defensive check - reflector raises exceptions but returns None could happen)
        if reflection is None:  # pyright: ignore[reportUnnecessaryComparison]
            logger.error(
                "Reflection failed: null response from reflector",
                extra={"iteration": self.iteration},
            )
            return AgentRunResult(
                output="Orchestration failed: reflection returned no result",
                status=AgentStatus.FAILED,
            )

        if reflection.done:
            logger.info(
                "Goal accomplished",
                extra={
                    "iteration": self.iteration,
                    "completed_tasks": len(self.todo.get_done()),
                },
            )

            # Checkpoint: transition to DONE phase
            if self._run_store is not None and self._run_id is not None:
                self._run_store.update_loop_state(self._run_id, Phase.DONE, self.iteration, None)

            return AgentRunResult(
                output=self._synthesize_result(),
                status=AgentStatus.COMPLETED,
            )

        # Update tasks based on reflection
        self._apply_reflection(reflection)
        return None

    def _apply_reflection(self, reflection: ReflectionOutput) -> None:
        """Apply reflection results: add validated tasks, cancel irrelevant ones."""
        if reflection.new_tasks:
            # Validate task descriptions for injection prevention
            validated_tasks = [task for task in reflection.new_tasks if self.validate_task_description(task)]

            if len(validated_tasks) < len(reflection.new_tasks):
                logger.warning(
                    "Some reflection tasks rejected due to suspicious patterns",
                    extra={
                        "rejected_count": len(reflection.new_tasks) - len(validated_tasks),
                        "total": len(reflection.new_tasks),
                        "iteration": self.iteration,
                    },
                )

            if validated_tasks:
                new_ids = self.todo.add_tasks(validated_tasks)
                logger.info(
                    "New tasks added from reflection",
                    extra={"count": len(new_ids)},
                )

        for task_id in reflection.complete_ids:
            if task_id in self.todo.tasks:
                self.todo.tasks[task_id].status = TaskStatus.CANCELLED
            else:
                logger.warning(
                    "Reflection recommended cancelling non-existent task",
                    extra={
                        "task_id": task_id,
                        "total_tasks": len(self.todo.tasks),
                        "iteration": self.iteration,
                    },
                )

    def validate_task_description(self, description: str) -> bool:
        """
        Validate task description for suspicious patterns (injection prevention).

        Args:
            description: Task description to validate

        Returns:
            True if description is safe, False if it contains suspicious patterns
        """
        # Patterns that might indicate injection attempts
        suspicious_patterns = [
            r"[;|&$`]",  # Shell metacharacters
            r"\brm\s+(-r|-f|--)",  # Destructive commands
            r"\b(del|drop|truncate)\s+(table|database)",  # Database destruction
            r"\bexec\s*\(",  # Python exec
            r"\beval\s*\(",  # Python eval
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, description, re.IGNORECASE):
                logger.debug(
                    "Task description rejected for suspicious pattern",
                    extra={"pattern": pattern, "description": description[:100]},
                )
                return False

        return True

    def _synthesize_result(self) -> str:
        """
        Synthesize execution results into final output.

        Aggregates completed tasks and their results into a summary.

        Returns:
            String describing all completed work and results
        """
        completed = self.todo.get_done()
        if not completed:
            return "No tasks completed."

        result_lines = [f"Completed {len(completed)} task(s):"]
        for i, task in enumerate(completed, 1):
            result_lines.append(f"{i}. {task.description}")
            if task.result:
                # Truncate long results
                truncated = task.result[:200] + "..." if len(task.result) > 200 else task.result
                result_lines.append(f"   Result: {truncated}")

        return "\n".join(result_lines)
