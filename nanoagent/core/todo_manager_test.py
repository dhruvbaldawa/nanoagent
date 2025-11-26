# ABOUTME: Unit tests for TodoManager task queue implementation
# ABOUTME: Validates priority-based task ordering and completion tracking

import pytest
from _pytest.logging import LogCaptureFixture

from nanoagent.core.todo_manager import TodoManager
from nanoagent.models.schemas import TaskStatus


class TestTodoManager:
    """Test suite for TodoManager class"""

    def test_empty_manager_returns_none(self):
        """Empty manager returns None for get_next"""
        manager = TodoManager()
        assert manager.get_next() is None

    def test_add_single_task(self):
        """Adding a single task returns it as pending"""
        manager = TodoManager()
        manager.add_tasks(["Test task"])
        pending = manager.get_pending()
        assert len(pending) == 1
        assert pending[0].description == "Test task"
        assert pending[0].status == TaskStatus.PENDING

    def test_add_multiple_tasks(self):
        """Multiple tasks added correctly"""
        manager = TodoManager()
        manager.add_tasks(["Task 1", "Task 2", "Task 3"])
        pending = manager.get_pending()
        assert len(pending) == 3

    def test_get_next_returns_highest_priority(self):
        """get_next returns highest priority pending task"""
        manager = TodoManager()
        manager.add_tasks(["Low priority"], priority=1)
        manager.add_tasks(["High priority"], priority=10)
        manager.add_tasks(["Medium priority"], priority=5)

        next_task = manager.get_next()
        assert next_task is not None
        assert next_task.description == "High priority"

    def test_get_next_returns_first_when_same_priority(self):
        """When multiple tasks have same priority, return first added"""
        manager = TodoManager()
        task1_id = manager.add_tasks(["Task 1"], priority=5)[0]
        manager.add_tasks(["Task 2"], priority=5)

        next_task = manager.get_next()
        assert next_task is not None
        assert next_task.id == task1_id

    def test_mark_done_transitions_task_status(self):
        """mark_done changes task status to done"""
        manager = TodoManager()
        task_ids = manager.add_tasks(["Task to complete"])
        task_id = task_ids[0]

        manager.mark_done(task_id, "Completed successfully")
        done_tasks = manager.get_done()
        assert len(done_tasks) == 1
        assert done_tasks[0].id == task_id
        assert done_tasks[0].status == TaskStatus.DONE

    def test_mark_done_removes_from_pending(self):
        """Completed task no longer appears in pending"""
        manager = TodoManager()
        task_ids = manager.add_tasks(["Task to complete"])
        task_id = task_ids[0]

        manager.mark_done(task_id, "Done")
        pending = manager.get_pending()
        assert len(pending) == 0

    def test_mark_done_nonexistent_task_raises_error(self):
        """Marking nonexistent task ID raises ValueError"""
        manager = TodoManager()
        manager.add_tasks(["Task"])

        # Should raise ValueError
        with pytest.raises(ValueError, match="Cannot mark nonexistent"):
            manager.mark_done("nonexistent", "result")

        # Pending should remain unchanged
        pending = manager.get_pending()
        assert len(pending) == 1

    def test_get_pending_excludes_done_tasks(self):
        """get_pending excludes completed tasks"""
        manager = TodoManager()
        task_ids = manager.add_tasks(["Task 1", "Task 2"])

        manager.mark_done(task_ids[0], "Done")
        pending = manager.get_pending()

        assert len(pending) == 1
        assert pending[0].id == task_ids[1]

    def test_get_done_tracks_completed_tasks(self):
        """get_done returns all completed tasks"""
        manager = TodoManager()
        task_ids = manager.add_tasks(["Task 1", "Task 2", "Task 3"])

        manager.mark_done(task_ids[0], "Completed")
        manager.mark_done(task_ids[2], "Done")

        done = manager.get_done()
        assert len(done) == 2
        assert {t.id for t in done} == {task_ids[0], task_ids[2]}

    def test_add_tasks_returns_task_ids(self):
        """add_tasks returns list of created task IDs"""
        manager = TodoManager()
        task_ids = manager.add_tasks(["Task 1", "Task 2"])

        assert len(task_ids) == 2
        assert all(isinstance(tid, str) for tid in task_ids)

    def test_priority_range_respected(self):
        """Tasks respect priority range 1-10"""
        manager = TodoManager()
        manager.add_tasks(["Task"], priority=1)
        manager.add_tasks(["Task"], priority=5)
        manager.add_tasks(["Task"], priority=10)

        tasks = manager.get_pending()
        assert len(tasks) == 3

    def test_multiple_priority_levels_sorted_correctly(self):
        """Multiple tasks at different priorities sorted highest first"""
        manager = TodoManager()
        id3 = manager.add_tasks(["Priority 3"], priority=3)[0]
        manager.add_tasks(["Priority 1"], priority=1)
        id5 = manager.add_tasks(["Priority 5"], priority=5)[0]

        next_task = manager.get_next()
        assert next_task is not None
        assert next_task.description == "Priority 5"
        manager.mark_done(id5, "Done")

        next_task = manager.get_next()
        assert next_task is not None
        assert next_task.description == "Priority 3"
        manager.mark_done(id3, "Done")

        next_task = manager.get_next()
        assert next_task is not None
        assert next_task.description == "Priority 1"

    def test_get_next_skips_completed_tasks(self):
        """get_next skips completed tasks"""
        manager = TodoManager()
        task_ids = manager.add_tasks(["Task 1"], priority=10)
        manager.add_tasks(["Task 2"], priority=5)

        # Mark first task done
        manager.mark_done(task_ids[0], "Done")

        # Should return Task 2 now
        next_task = manager.get_next()
        assert next_task is not None
        assert next_task.description == "Task 2"

    def test_default_priority_is_five(self):
        """Tasks default to priority 5"""
        manager = TodoManager()
        manager.add_tasks(["Task without priority"])

        task = manager.get_next()
        assert task is not None
        assert task.priority == 5

    def test_cancelled_tasks_excluded_from_pending(self):
        """Cancelled tasks should not appear in pending or done lists"""
        manager = TodoManager()
        task_id = manager.add_tasks(["Task"])[0]
        manager.tasks[task_id].status = TaskStatus.CANCELLED

        assert manager.get_next() is None
        assert len(manager.get_pending()) == 0
        assert len(manager.get_done()) == 0

    def test_result_stored_in_task(self):
        """mark_done stores execution result in task"""
        manager = TodoManager()
        task_id = manager.add_tasks(["Task"])[0]

        manager.mark_done(task_id, "Execution completed successfully")

        done_task = manager.get_done()[0]
        assert done_task.result == "Execution completed successfully"

    def test_mark_done_nonexistent_logs_error_and_raises(self, caplog: LogCaptureFixture) -> None:
        """mark_done logs error and raises ValueError for nonexistent task_id"""
        manager = TodoManager()
        manager.add_tasks(["Task"])

        with caplog.at_level("ERROR"):
            with pytest.raises(ValueError, match="Cannot mark nonexistent"):
                manager.mark_done("nonexistent", "result")

        assert "Cannot mark nonexistent task as done" in caplog.text
        assert "nonexistent" in caplog.text
