# ABOUTME: Protocol definitions for persistence stores
# ABOUTME: Composable interfaces following single responsibility principle

from datetime import datetime
from enum import Enum
from typing import Protocol

from pydantic import BaseModel, Field

from nanoagent.models.schemas import Task


class Phase(str, Enum):
    """Orchestration loop phases for checkpoint/resume"""

    PLANNING = "planning"
    EXECUTING = "executing"
    REFLECTING = "reflecting"
    DONE = "done"


class RunState(BaseModel):
    """State of an orchestration run"""

    run_id: str = Field(..., description="Unique run identifier")
    goal: str = Field(..., description="High-level goal")
    max_iterations: int = Field(..., ge=1, description="Maximum iterations")
    phase: Phase = Field(default=Phase.PLANNING, description="Current loop phase")
    iteration: int = Field(default=0, ge=0, description="Current iteration count")
    current_task_id: str | None = Field(default=None, description="Task being executed (for resume)")
    created_at: datetime = Field(default_factory=datetime.now, description="Run creation timestamp")


class RunStore(Protocol):
    """Protocol for run lifecycle and loop state management"""

    def create(self, run_id: str, goal: str, max_iterations: int) -> None:
        """Create a new run"""
        ...

    def get(self, run_id: str) -> RunState | None:
        """Get run state by ID, returns None if not found"""
        ...

    def list_runs(self) -> list[str]:
        """List all run IDs"""
        ...

    def update_loop_state(
        self,
        run_id: str,
        phase: Phase,
        iteration: int,
        current_task_id: str | None,
    ) -> None:
        """Update loop state for checkpointing"""
        ...


class TaskStore(Protocol):
    """Protocol for task persistence"""

    def save_task(self, run_id: str, task: Task) -> None:
        """Save or update a task"""
        ...

    def get_all_tasks(self, run_id: str) -> list[Task]:
        """Get all tasks for a run"""
        ...

    def get_pending_tasks(self, run_id: str) -> list[Task]:
        """Get pending tasks for a run, ordered by priority (descending)"""
        ...


class ContextStore(Protocol):
    """Protocol for execution context (task results) persistence"""

    def save_result(self, run_id: str, task_id: str, result: str) -> None:
        """Save task execution result"""
        ...

    def get_all_results(self, run_id: str) -> dict[str, str]:
        """Get all results for a run as task_id -> result mapping"""
        ...
