# ABOUTME: Manages task queue with priority-based ordering and completion tracking
# ABOUTME: Plain Python task management for orchestrating agent workflows

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from nanoagent.models.schemas import Task, TaskStatus

if TYPE_CHECKING:
    from nanoagent.persistence.protocols import TaskStore

logger = logging.getLogger(__name__)


class TodoManager:
    """
    Manages a task queue with priority-based ordering and completion tracking.
    Tasks are stored by ID and ordered by priority (highest first).

    Supports two modes:
    - Standalone mode (default): In-memory storage, no persistence
    - Persistent mode: Delegates to TaskStore when store + run_id provided
    """

    def __init__(
        self,
        store: TaskStore | None = None,
        run_id: str | None = None,
    ) -> None:
        """
        Initialize task manager.

        Args:
            store: Optional TaskStore for persistence
            run_id: Required when store is provided, scopes tasks to this run

        Raises:
            ValueError: If store provided without run_id or vice versa
        """
        if store is not None and run_id is None:
            raise ValueError("run_id is required when store is provided")
        if run_id is not None and store is None:
            raise ValueError("store is required when run_id is provided")

        self._store = store
        self._run_id = run_id

        # In-memory storage for standalone mode
        self.tasks: dict[str, Task] = {}

    def add_tasks(self, descriptions: list[str], priority: int = 5) -> list[str]:
        """
        Add tasks to the queue with specified priority.

        Args:
            descriptions: List of task descriptions
            priority: Priority level (1-10, default 5)

        Returns:
            List of created task IDs
        """
        task_ids: list[str] = []
        for description in descriptions:
            task = Task(description=description, priority=priority)
            if self._store is not None and self._run_id is not None:
                self._store.save_task(self._run_id, task)
            else:
                self.tasks[task.id] = task
            task_ids.append(task.id)
        return task_ids

    def get_next(self) -> Task | None:
        """
        Return highest priority pending task.

        Returns:
            Task with highest priority among pending tasks, or None if queue is empty
        """
        if self._store is not None and self._run_id is not None:
            # Store returns pending tasks already sorted by priority (descending)
            pending_tasks = self._store.get_pending_tasks(self._run_id)
            return pending_tasks[0] if pending_tasks else None

        pending_tasks = [t for t in self.tasks.values() if t.status == TaskStatus.PENDING]
        if not pending_tasks:
            return None
        # Sort by priority (descending), then by insertion order (task ID)
        sorted_tasks = sorted(pending_tasks, key=lambda t: (-t.priority, self.tasks[t.id] is t))
        return sorted_tasks[0]

    def mark_done(self, task_id: str, result: str) -> None:
        """
        Mark a task as complete.

        Args:
            task_id: ID of task to mark done
            result: Result/output of the task execution

        Raises:
            ValueError: If task_id does not exist in task queue
        """
        if self._store is not None and self._run_id is not None:
            # Find task in store, update status, and save
            all_tasks = self._store.get_all_tasks(self._run_id)
            task = next((t for t in all_tasks if t.id == task_id), None)
            if task is None:
                logger.error(
                    "Cannot mark nonexistent task as done",
                    extra={"task_id": task_id, "run_id": self._run_id},
                )
                raise ValueError(f"Cannot mark nonexistent task as done: {task_id}")
            task.status = TaskStatus.DONE
            task.result = result
            self._store.save_task(self._run_id, task)
            return

        if task_id not in self.tasks:
            logger.error(
                "Cannot mark nonexistent task as done",
                extra={"task_id": task_id, "total_tasks": len(self.tasks)},
            )
            raise ValueError(f"Cannot mark nonexistent task as done: {task_id} (total tasks: {len(self.tasks)})")

        self.tasks[task_id].status = TaskStatus.DONE
        self.tasks[task_id].result = result

    def get_pending(self) -> list[Task]:
        """
        Get all pending tasks.

        Returns:
            List of tasks with PENDING status
        """
        if self._store is not None and self._run_id is not None:
            return self._store.get_pending_tasks(self._run_id)
        return [t for t in self.tasks.values() if t.status == TaskStatus.PENDING]

    def get_done(self) -> list[Task]:
        """
        Get all completed tasks.

        Returns:
            List of tasks with DONE status
        """
        if self._store is not None and self._run_id is not None:
            return [t for t in self._store.get_all_tasks(self._run_id) if t.status == TaskStatus.DONE]
        return [t for t in self.tasks.values() if t.status == TaskStatus.DONE]
