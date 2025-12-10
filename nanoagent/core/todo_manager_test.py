# ABOUTME: Unit tests for TodoManager task queue implementation
# ABOUTME: Validates priority-based task ordering and completion tracking

import pathlib

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


class TestTodoManagerPersistence:
    """Test TodoManager with TaskStore persistence"""

    def test_store_without_run_id_raises_error(self):
        """Providing store without run_id raises ValueError"""
        from nanoagent.persistence import MemoryStore

        store = MemoryStore()
        with pytest.raises(ValueError, match="run_id.*required"):
            TodoManager(store=store)

    def test_run_id_without_store_raises_error(self):
        """Providing run_id without store raises ValueError"""
        with pytest.raises(ValueError, match="store.*required"):
            TodoManager(run_id="test-run")

    def test_add_tasks_persists_to_store(self):
        """add_tasks saves tasks to store when provided"""
        from nanoagent.persistence import MemoryStore

        store = MemoryStore()
        store.create("test-run", "test goal", 10)
        manager = TodoManager(store=store, run_id="test-run")

        task_ids = manager.add_tasks(["Task 1", "Task 2"])

        # Verify tasks are in store
        stored_tasks = store.get_all_tasks("test-run")
        assert len(stored_tasks) == 2
        assert {t.id for t in stored_tasks} == set(task_ids)

    def test_get_next_reads_from_store(self):
        """get_next returns highest priority pending task from store"""
        from nanoagent.persistence import MemoryStore

        store = MemoryStore()
        store.create("test-run", "test goal", 10)
        manager = TodoManager(store=store, run_id="test-run")

        manager.add_tasks(["Low priority"], priority=1)
        manager.add_tasks(["High priority"], priority=10)

        next_task = manager.get_next()
        assert next_task is not None
        assert next_task.description == "High priority"

    def test_mark_done_updates_store(self):
        """mark_done updates task status in store"""
        from nanoagent.persistence import MemoryStore

        store = MemoryStore()
        store.create("test-run", "test goal", 10)
        manager = TodoManager(store=store, run_id="test-run")

        task_id = manager.add_tasks(["Task"])[0]
        manager.mark_done(task_id, "Completed")

        # Verify status updated in store
        stored_tasks = store.get_all_tasks("test-run")
        done_task = next(t for t in stored_tasks if t.id == task_id)
        assert done_task.status == TaskStatus.DONE
        assert done_task.result == "Completed"

    def test_get_pending_reads_from_store(self):
        """get_pending returns pending tasks from store"""
        from nanoagent.persistence import MemoryStore

        store = MemoryStore()
        store.create("test-run", "test goal", 10)
        manager = TodoManager(store=store, run_id="test-run")

        manager.add_tasks(["Task 1", "Task 2"])
        task_id = manager.add_tasks(["Task 3"])[0]
        manager.mark_done(task_id, "Done")

        pending = manager.get_pending()
        assert len(pending) == 2

    def test_get_done_reads_from_store(self):
        """get_done returns completed tasks from store"""
        from nanoagent.persistence import MemoryStore

        store = MemoryStore()
        store.create("test-run", "test goal", 10)
        manager = TodoManager(store=store, run_id="test-run")

        task_ids = manager.add_tasks(["Task 1", "Task 2", "Task 3"])
        manager.mark_done(task_ids[0], "Done 1")
        manager.mark_done(task_ids[2], "Done 3")

        done = manager.get_done()
        assert len(done) == 2
        assert {t.id for t in done} == {task_ids[0], task_ids[2]}

    def test_tasks_persist_across_instances(self):
        """Tasks persist across TodoManager instances with same store + run_id"""
        from nanoagent.persistence import MemoryStore

        store = MemoryStore()
        store.create("test-run", "test goal", 10)

        # First instance adds tasks
        manager1 = TodoManager(store=store, run_id="test-run")
        task_id = manager1.add_tasks(["Persistent task"])[0]

        # Second instance sees the task
        manager2 = TodoManager(store=store, run_id="test-run")
        pending = manager2.get_pending()
        assert len(pending) == 1
        assert pending[0].id == task_id
        assert pending[0].description == "Persistent task"

    def test_completion_persists_across_instances(self):
        """Task completion persists across TodoManager instances"""
        from nanoagent.persistence import MemoryStore

        store = MemoryStore()
        store.create("test-run", "test goal", 10)

        # First instance adds and completes task
        manager1 = TodoManager(store=store, run_id="test-run")
        task_id = manager1.add_tasks(["Task"])[0]
        manager1.mark_done(task_id, "Completed")

        # Second instance sees completion
        manager2 = TodoManager(store=store, run_id="test-run")
        assert len(manager2.get_pending()) == 0
        done = manager2.get_done()
        assert len(done) == 1
        assert done[0].result == "Completed"

    def test_works_with_sqlite_store(self, tmp_path: pathlib.Path):
        """TodoManager works with SQLiteStore"""
        from nanoagent.persistence import SQLiteStore

        db_path = tmp_path / "test.db"
        store = SQLiteStore(str(db_path))
        store.create("test-run", "test goal", 10)

        manager = TodoManager(store=store, run_id="test-run")
        task_ids = manager.add_tasks(["Task 1", "Task 2"])
        manager.mark_done(task_ids[0], "Done")

        assert len(manager.get_pending()) == 1
        assert len(manager.get_done()) == 1

        store.close()

    def test_priority_ordering_matches_inmemory_mode(self):
        """Priority ordering in persistent mode matches in-memory mode"""
        from nanoagent.persistence import MemoryStore

        store = MemoryStore()
        store.create("test-run", "test goal", 10)
        manager = TodoManager(store=store, run_id="test-run")

        # Add tasks in specific order
        manager.add_tasks(["Priority 3"], priority=3)
        manager.add_tasks(["Priority 5"], priority=5)
        manager.add_tasks(["Priority 1"], priority=1)

        # Should return highest priority first
        task1 = manager.get_next()
        assert task1 is not None
        assert task1.description == "Priority 5"

        manager.mark_done(task1.id, "Done")
        task2 = manager.get_next()
        assert task2 is not None
        assert task2.description == "Priority 3"

    def test_mark_done_nonexistent_in_persistent_mode(self):
        """mark_done raises ValueError for nonexistent task in persistent mode"""
        from nanoagent.persistence import MemoryStore

        store = MemoryStore()
        store.create("test-run", "test goal", 10)
        manager = TodoManager(store=store, run_id="test-run")

        with pytest.raises(ValueError, match="Cannot mark nonexistent"):
            manager.mark_done("nonexistent-id", "result")

    def test_empty_store_returns_none(self):
        """get_next returns None when store has no tasks"""
        from nanoagent.persistence import MemoryStore

        store = MemoryStore()
        store.create("test-run", "test goal", 10)
        manager = TodoManager(store=store, run_id="test-run")

        assert manager.get_next() is None
        assert manager.get_pending() == []
        assert manager.get_done() == []
