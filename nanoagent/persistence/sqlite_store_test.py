# ABOUTME: Tests for SQLite persistence store
# ABOUTME: Validates round-trip persistence, isolation, and concurrent access

import threading
import time
from collections.abc import Iterator
from pathlib import Path

import pytest

from nanoagent.models.schemas import Task, TaskStatus
from nanoagent.persistence.protocols import Phase
from nanoagent.persistence.sqlite_store import SQLiteStore


@pytest.fixture
def store(tmp_path: Path) -> Iterator[SQLiteStore]:
    """Create a temporary SQLite store for testing"""
    db_path = tmp_path / "test.db"
    s = SQLiteStore(db_path)
    yield s
    s.close()


@pytest.fixture
def memory_store() -> Iterator[SQLiteStore]:
    """Create an in-memory SQLite store for testing"""
    s = SQLiteStore(":memory:")
    yield s
    s.close()


class TestRunStore:
    """Tests for RunStore protocol implementation"""

    def test_create_and_get_run(self, store: SQLiteStore) -> None:
        """Create a run and retrieve it"""
        store.create("run-1", "Test goal", 10)

        state = store.get("run-1")
        assert state is not None
        assert state.run_id == "run-1"
        assert state.goal == "Test goal"
        assert state.max_iterations == 10
        assert state.phase == Phase.PLANNING
        assert state.iteration == 0
        assert state.current_task_id is None

    def test_get_nonexistent_run(self, store: SQLiteStore) -> None:
        """Getting a non-existent run returns None"""
        state = store.get("nonexistent")
        assert state is None

    def test_list_runs(self, store: SQLiteStore) -> None:
        """List all runs"""
        store.create("run-a", "Goal A", 5)
        store.create("run-b", "Goal B", 10)

        runs = store.list_runs()
        assert len(runs) == 2
        assert "run-a" in runs
        assert "run-b" in runs

    def test_list_empty(self, store: SQLiteStore) -> None:
        """List returns empty when no runs exist"""
        runs = store.list_runs()
        assert runs == []

    def test_update_loop_state(self, store: SQLiteStore) -> None:
        """Update loop state for checkpointing"""
        store.create("run-1", "Goal", 10)

        store.update_loop_state("run-1", Phase.EXECUTING, 3, "task-1")

        state = store.get("run-1")
        assert state is not None
        assert state.phase == Phase.EXECUTING
        assert state.iteration == 3
        assert state.current_task_id == "task-1"

    def test_update_loop_state_clear_task(self, store: SQLiteStore) -> None:
        """Update loop state clearing current task"""
        store.create("run-1", "Goal", 10)
        store.update_loop_state("run-1", Phase.EXECUTING, 1, "task-1")
        store.update_loop_state("run-1", Phase.EXECUTING, 2, None)

        state = store.get("run-1")
        assert state is not None
        assert state.current_task_id is None


class TestTaskStore:
    """Tests for TaskStore protocol implementation"""

    def test_save_and_get_task(self, store: SQLiteStore) -> None:
        """Save a task and retrieve it"""
        store.create("run-1", "Goal", 10)

        task = Task(id="task-001", description="Do something", priority=7)
        store.save_task("run-1", task)

        tasks = store.get_all_tasks("run-1")
        assert len(tasks) == 1
        assert tasks[0].id == "task-001"
        assert tasks[0].description == "Do something"
        assert tasks[0].priority == 7
        assert tasks[0].status == TaskStatus.PENDING

    def test_save_updates_existing_task(self, store: SQLiteStore) -> None:
        """Saving a task with same ID updates it"""
        store.create("run-1", "Goal", 10)

        task = Task(id="task-001", description="Original")
        store.save_task("run-1", task)

        updated = Task(id="task-001", description="Updated", status=TaskStatus.DONE, result="Done!")
        store.save_task("run-1", updated)

        tasks = store.get_all_tasks("run-1")
        assert len(tasks) == 1
        assert tasks[0].description == "Updated"
        assert tasks[0].status == TaskStatus.DONE
        assert tasks[0].result == "Done!"

    def test_get_pending_tasks(self, store: SQLiteStore) -> None:
        """Get only pending tasks"""
        store.create("run-1", "Goal", 10)

        store.save_task("run-1", Task(id="task-001", description="Pending 1", status=TaskStatus.PENDING))
        store.save_task("run-1", Task(id="task-002", description="Done", status=TaskStatus.DONE))
        store.save_task("run-1", Task(id="task-003", description="Pending 2", status=TaskStatus.PENDING))

        pending = store.get_pending_tasks("run-1")
        assert len(pending) == 2
        assert all(t.status == TaskStatus.PENDING for t in pending)

    def test_get_pending_ordered_by_priority(self, store: SQLiteStore) -> None:
        """Pending tasks are ordered by priority descending"""
        store.create("run-1", "Goal", 10)

        store.save_task("run-1", Task(id="tasklow0", description="Low priority", priority=3))
        store.save_task("run-1", Task(id="taskhigh", description="High priority", priority=9))
        store.save_task("run-1", Task(id="taskmid0", description="Mid priority", priority=5))

        pending = store.get_pending_tasks("run-1")
        assert len(pending) == 3
        assert pending[0].id == "taskhigh"
        assert pending[1].id == "taskmid0"
        assert pending[2].id == "tasklow0"

    def test_get_all_empty(self, store: SQLiteStore) -> None:
        """Get all returns empty list when no tasks"""
        store.create("run-1", "Goal", 10)
        tasks = store.get_all_tasks("run-1")
        assert tasks == []


class TestContextStore:
    """Tests for ContextStore protocol implementation"""

    def test_save_and_get_result(self, store: SQLiteStore) -> None:
        """Save a result and retrieve it"""
        store.create("run-1", "Goal", 10)

        store.save_result("run-1", "task-1", "Result 1")
        store.save_result("run-1", "task-2", "Result 2")

        context = store.get_all_results("run-1")
        assert context == {"task-1": "Result 1", "task-2": "Result 2"}

    def test_save_result_updates_existing(self, store: SQLiteStore) -> None:
        """Saving result with same task_id updates it"""
        store.create("run-1", "Goal", 10)

        store.save_result("run-1", "task-1", "Original")
        store.save_result("run-1", "task-1", "Updated")

        context = store.get_all_results("run-1")
        assert context == {"task-1": "Updated"}

    def test_get_all_results_empty(self, store: SQLiteStore) -> None:
        """Get all returns empty dict when no results"""
        store.create("run-1", "Goal", 10)
        context = store.get_all_results("run-1")
        assert context == {}


class TestEdgeCases:
    """Tests for edge cases and error handling"""

    def test_duplicate_run_id_raises(self, store: SQLiteStore) -> None:
        """Creating a run with duplicate ID raises IntegrityError"""
        import sqlite3

        store.create("run-1", "Goal", 10)

        with pytest.raises(sqlite3.IntegrityError):
            store.create("run-1", "Different goal", 5)

    def test_get_tasks_nonexistent_run(self, store: SQLiteStore) -> None:
        """Getting tasks for non-existent run returns empty list"""
        tasks = store.get_all_tasks("nonexistent")
        assert tasks == []

    def test_get_results_nonexistent_run(self, store: SQLiteStore) -> None:
        """Getting results for non-existent run returns empty dict"""
        results = store.get_all_results("nonexistent")
        assert results == {}

    def test_close_idempotent(self, store: SQLiteStore) -> None:
        """Calling close multiple times is safe"""
        store.close()
        store.close()  # Should not raise

    def test_update_loop_state_nonexistent_run(self, store: SQLiteStore) -> None:
        """Updating loop state for non-existent run silently does nothing"""
        # This doesn't raise - it just updates 0 rows
        store.update_loop_state("nonexistent", Phase.EXECUTING, 1, None)
        # Verify no run was created
        assert store.get("nonexistent") is None


class TestSecurity:
    """Tests for security features"""

    def test_path_traversal_blocked(self, tmp_path: Path) -> None:
        """Path traversal attempts are rejected when allowed_dir is set"""
        with pytest.raises(ValueError, match="escapes allowed directory"):
            SQLiteStore("../../../etc/passwd.db", allowed_dir=tmp_path)

    def test_path_traversal_absolute_blocked(self, tmp_path: Path) -> None:
        """Absolute paths outside allowed_dir are rejected"""
        # Use a path guaranteed to be outside tmp_path
        outside_path = (tmp_path.parent / "outside.db").resolve()
        with pytest.raises(ValueError, match="escapes allowed directory"):
            SQLiteStore(str(outside_path), allowed_dir=tmp_path)

    def test_path_within_allowed_dir_works(self, tmp_path: Path) -> None:
        """Paths within allowed_dir work correctly"""
        store = SQLiteStore("test.db", allowed_dir=tmp_path)
        store.create("run-1", "Goal", 10)
        assert store.get("run-1") is not None
        store.close()

    def test_memory_db_always_allowed(self, tmp_path: Path) -> None:
        """:memory: database works regardless of allowed_dir"""
        store = SQLiteStore(":memory:", allowed_dir=tmp_path)
        store.create("run-1", "Goal", 10)
        assert store.get("run-1") is not None
        store.close()

    def test_foreign_key_constraint_enforced(self, store: SQLiteStore) -> None:
        """Foreign key constraints prevent orphaned tasks"""
        import sqlite3

        # Saving a task for non-existent run should fail with FK enabled
        with pytest.raises(sqlite3.IntegrityError):
            store.save_task("nonexistent-run", Task(id="task0001", description="Orphan task"))

    def test_foreign_key_constraint_context(self, store: SQLiteStore) -> None:
        """Foreign key constraints prevent orphaned context results"""
        import sqlite3

        # Saving a result for non-existent run should fail with FK enabled
        with pytest.raises(sqlite3.IntegrityError):
            store.save_result("nonexistent-run", "task0001", "Orphan result")


class TestIsolation:
    """Tests for run_id isolation"""

    def test_tasks_isolated_by_run_id(self, store: SQLiteStore) -> None:
        """Tasks from different runs don't interfere"""
        store.create("run-a", "Goal A", 10)
        store.create("run-b", "Goal B", 10)

        store.save_task("run-a", Task(id="task0001", description="Task for A"))
        store.save_task("run-b", Task(id="task0001", description="Task for B"))  # Same task ID, different run

        tasks_a = store.get_all_tasks("run-a")
        tasks_b = store.get_all_tasks("run-b")

        assert len(tasks_a) == 1
        assert len(tasks_b) == 1
        assert tasks_a[0].description == "Task for A"
        assert tasks_b[0].description == "Task for B"

    def test_context_isolated_by_run_id(self, store: SQLiteStore) -> None:
        """Context from different runs don't interfere"""
        store.create("run-a", "Goal A", 10)
        store.create("run-b", "Goal B", 10)

        store.save_result("run-a", "task0001", "Result A")
        store.save_result("run-b", "task0001", "Result B")

        context_a = store.get_all_results("run-a")
        context_b = store.get_all_results("run-b")

        assert context_a == {"task0001": "Result A"}
        assert context_b == {"task0001": "Result B"}


class TestConcurrentAccess:
    """Tests for concurrent access patterns"""

    def test_concurrent_reads(self, tmp_path: Path) -> None:
        """Multiple readers can access simultaneously"""
        db_path = tmp_path / "concurrent.db"

        # Setup data
        store = SQLiteStore(db_path)
        store.create("run-1", "Goal", 10)
        for i in range(10):
            store.save_task("run-1", Task(id=f"task-{i:03d}", description=f"Task {i}"))
        store.close()

        results: list[int] = []
        errors: list[Exception] = []

        def read_tasks() -> None:
            try:
                reader = SQLiteStore(db_path)
                tasks = reader.get_all_tasks("run-1")
                results.append(len(tasks))
                reader.close()
            except Exception as e:
                errors.append(e)

        # Start multiple readers
        threads = [threading.Thread(target=read_tasks) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Errors during concurrent reads: {errors}"
        assert all(r == 10 for r in results), f"Inconsistent read results: {results}"

    def test_independent_runs_concurrent(self, tmp_path: Path) -> None:
        """Different runs can be modified concurrently"""
        db_path = tmp_path / "concurrent.db"

        # Pre-create runs
        store = SQLiteStore(db_path)
        store.create("run-a", "Goal A", 10)
        store.create("run-b", "Goal B", 10)
        store.close()

        errors: list[Exception] = []

        def modify_run(run_id: str, count: int) -> None:
            try:
                s = SQLiteStore(db_path)
                for i in range(count):
                    s.save_task(run_id, Task(id=f"task-{i:03d}", description=f"Task {i}"))
                    time.sleep(0.01)  # Small delay to encourage interleaving
                s.close()
            except Exception as e:
                errors.append(e)

        t1 = threading.Thread(target=modify_run, args=("run-a", 5))
        t2 = threading.Thread(target=modify_run, args=("run-b", 5))

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert errors == [], f"Errors during concurrent modifications: {errors}"

        # Verify both runs have correct data
        store = SQLiteStore(db_path)
        tasks_a = store.get_all_tasks("run-a")
        tasks_b = store.get_all_tasks("run-b")
        store.close()

        assert len(tasks_a) == 5
        assert len(tasks_b) == 5


class TestRoundTrip:
    """Integration test for full round-trip persistence"""

    def test_full_orchestration_round_trip(self, store: SQLiteStore) -> None:
        """Test complete orchestration state persistence"""
        # Create run
        store.create("run-test", "Complete a complex goal", 20)

        # Add initial tasks
        tasks = [
            Task(id="task-001", description="Research", priority=9),
            Task(id="task-002", description="Analyze", priority=7),
            Task(id="task-003", description="Summarize", priority=5),
        ]
        for task in tasks:
            store.save_task("run-test", task)

        # Simulate execution
        store.update_loop_state("run-test", Phase.EXECUTING, 1, "task-001")

        # Complete first task
        tasks[0].status = TaskStatus.DONE
        tasks[0].result = "Research complete"
        store.save_task("run-test", tasks[0])
        store.save_result("run-test", "task-001", "Research findings...")
        store.update_loop_state("run-test", Phase.EXECUTING, 2, None)

        # Verify state
        state = store.get("run-test")
        assert state is not None
        assert state.phase == Phase.EXECUTING
        assert state.iteration == 2
        assert state.current_task_id is None

        all_tasks = store.get_all_tasks("run-test")
        assert len(all_tasks) == 3

        pending = store.get_pending_tasks("run-test")
        assert len(pending) == 2

        context = store.get_all_results("run-test")
        assert "task-001" in context
