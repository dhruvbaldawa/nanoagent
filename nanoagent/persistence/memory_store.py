# ABOUTME: Pure Python dict-based implementation of persistence protocols
# ABOUTME: Fast, no dependencies - ideal for unit tests and simple use cases

from datetime import datetime

from nanoagent.models.schemas import Task, TaskStatus
from nanoagent.persistence.protocols import ContextStore, Phase, RunState, RunStore, TaskStore


class MemoryStore(RunStore, TaskStore, ContextStore):
    """
    In-memory persistence store implementing all three protocols.

    Uses Python dicts for storage. Fast and simple, but not persistent across restarts.
    Useful for unit tests and scenarios where persistence isn't required.
    """

    def __init__(self) -> None:
        """Initialize empty in-memory store."""
        self._runs: dict[str, RunState] = {}
        self._tasks: dict[str, dict[str, Task]] = {}  # run_id -> {task_id -> Task}
        self._context: dict[str, dict[str, str]] = {}  # run_id -> {task_id -> result}

    # --- RunStore implementation ---

    def create(self, run_id: str, goal: str, max_iterations: int) -> None:
        """Create a new run. Raises KeyError if run_id already exists."""
        if run_id in self._runs:
            raise KeyError(f"Run '{run_id}' already exists")
        self._runs[run_id] = RunState(
            run_id=run_id,
            goal=goal,
            max_iterations=max_iterations,
            phase=Phase.PLANNING,
            iteration=0,
            current_task_id=None,
            created_at=datetime.now(),
        )
        self._tasks[run_id] = {}
        self._context[run_id] = {}

    def get(self, run_id: str) -> RunState | None:
        """Get run state by ID, returns None if not found."""
        return self._runs.get(run_id)

    def list_runs(self) -> list[str]:
        """List all run IDs, ordered by creation time (newest first)."""
        return sorted(
            self._runs.keys(),
            key=lambda rid: self._runs[rid].created_at,
            reverse=True,
        )

    def update_loop_state(
        self,
        run_id: str,
        phase: Phase,
        iteration: int,
        current_task_id: str | None,
    ) -> None:
        """Update loop state for checkpointing. No-op if run doesn't exist."""
        if run_id not in self._runs:
            return
        run = self._runs[run_id]
        self._runs[run_id] = run.model_copy(
            update={"phase": phase, "iteration": iteration, "current_task_id": current_task_id}
        )

    # --- TaskStore implementation ---

    def save_task(self, run_id: str, task: Task) -> None:
        """Save or update a task. Raises KeyError if run doesn't exist."""
        if run_id not in self._runs:
            raise KeyError(f"Run '{run_id}' does not exist")
        self._tasks[run_id][task.id] = task

    def get_all_tasks(self, run_id: str) -> list[Task]:
        """Get all tasks for a run, ordered by priority (descending)."""
        if run_id not in self._tasks:
            return []
        return sorted(self._tasks[run_id].values(), key=lambda t: t.priority, reverse=True)

    def get_pending_tasks(self, run_id: str) -> list[Task]:
        """Get pending tasks for a run, ordered by priority (descending)."""
        if run_id not in self._tasks:
            return []
        return sorted(
            [t for t in self._tasks[run_id].values() if t.status == TaskStatus.PENDING],
            key=lambda t: t.priority,
            reverse=True,
        )

    # --- ContextStore implementation ---

    def save_result(self, run_id: str, task_id: str, result: str) -> None:
        """Save task execution result. Raises KeyError if run doesn't exist."""
        if run_id not in self._runs:
            raise KeyError(f"Run '{run_id}' does not exist")
        self._context[run_id][task_id] = result

    def get_all_results(self, run_id: str) -> dict[str, str]:
        """Get all results for a run as task_id -> result mapping."""
        return dict(self._context.get(run_id, {}))
