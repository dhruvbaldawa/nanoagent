# ABOUTME: Manages task queue with priority-based ordering and completion tracking
# ABOUTME: Plain Python task management for orchestrating agent workflows

import logging

from nanoagent.models.schemas import Task, TaskStatus

logger = logging.getLogger(__name__)


class TodoManager:
    """
    Manages a task queue with priority-based ordering and completion tracking.
    Tasks are stored by ID and ordered by priority (highest first).
    """

    def __init__(self) -> None:
        """Initialize empty task manager"""
        self.tasks: dict[str, Task] = {}
        self.completed: set[str] = set()

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
            self.tasks[task.id] = task
            task_ids.append(task.id)
        return task_ids

    def get_next(self) -> Task | None:
        """
        Return highest priority pending task.

        Returns:
            Task with highest priority among pending tasks, or None if queue is empty
        """
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
        if task_id not in self.tasks:
            logger.error(
                "Cannot mark nonexistent task as done",
                extra={"task_id": task_id, "total_tasks": len(self.tasks), "completed_count": len(self.completed)},
            )
            raise ValueError(f"Cannot mark nonexistent task as done: {task_id} (total tasks: {len(self.tasks)})")

        self.tasks[task_id].status = TaskStatus.DONE
        self.tasks[task_id].result = result
        self.completed.add(task_id)

    def get_pending(self) -> list[Task]:
        """
        Get all pending tasks.

        Returns:
            List of tasks with PENDING status
        """
        return [t for t in self.tasks.values() if t.status == TaskStatus.PENDING]

    def get_done(self) -> list[Task]:
        """
        Get all completed tasks.

        Returns:
            List of tasks with DONE status
        """
        return [t for t in self.tasks.values() if t.status == TaskStatus.DONE]
