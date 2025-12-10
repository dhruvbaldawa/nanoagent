# ABOUTME: Tests for in-memory persistence store
# ABOUTME: Validates protocol compliance and behavior parity with SQLiteStore

from collections.abc import Iterator

import pytest

from nanoagent.models.schemas import Task, TaskStatus
from nanoagent.persistence.memory_store import MemoryStore
from nanoagent.persistence.protocols import Phase


@pytest.fixture
def store() -> Iterator[MemoryStore]:
    """Create a fresh MemoryStore for testing."""
    yield MemoryStore()


class TestRunStore:
    """Tests for RunStore protocol implementation."""

    def test_create_and_get_run(self, store: MemoryStore) -> None:
        """Create a run and retrieve it."""
        store.create("run-1", "Test goal", 10)

        state = store.get("run-1")
        assert state is not None
        assert state.run_id == "run-1"
        assert state.goal == "Test goal"
        assert state.max_iterations == 10
        assert state.phase == Phase.PLANNING
        assert state.iteration == 0
        assert state.current_task_id is None

    def test_get_nonexistent_run(self, store: MemoryStore) -> None:
        """Getting a non-existent run returns None."""
        state = store.get("nonexistent")
        assert state is None

    def test_list_runs(self, store: MemoryStore) -> None:
        """List all runs."""
        store.create("run-a", "Goal A", 5)
        store.create("run-b", "Goal B", 10)

        runs = store.list_runs()
        assert len(runs) == 2
        assert "run-a" in runs
        assert "run-b" in runs

    def test_list_empty(self, store: MemoryStore) -> None:
        """List returns empty when no runs exist."""
        runs = store.list_runs()
        assert runs == []

    def test_update_loop_state(self, store: MemoryStore) -> None:
        """Update loop state for checkpointing."""
        store.create("run-1", "Goal", 10)

        store.update_loop_state("run-1", Phase.EXECUTING, 3, "task-1")

        state = store.get("run-1")
        assert state is not None
        assert state.phase == Phase.EXECUTING
        assert state.iteration == 3
        assert state.current_task_id == "task-1"

    def test_update_loop_state_clear_task(self, store: MemoryStore) -> None:
        """Update loop state clearing current task."""
        store.create("run-1", "Goal", 10)
        store.update_loop_state("run-1", Phase.EXECUTING, 1, "task-1")
        store.update_loop_state("run-1", Phase.EXECUTING, 2, None)

        state = store.get("run-1")
        assert state is not None
        assert state.current_task_id is None


class TestTaskStore:
    """Tests for TaskStore protocol implementation."""

    def test_save_and_get_task(self, store: MemoryStore) -> None:
        """Save a task and retrieve it."""
        store.create("run-1", "Goal", 10)

        task = Task(id="task-001", description="Do something", priority=7)
        store.save_task("run-1", task)

        tasks = store.get_all_tasks("run-1")
        assert len(tasks) == 1
        assert tasks[0].id == "task-001"
        assert tasks[0].description == "Do something"
        assert tasks[0].priority == 7
        assert tasks[0].status == TaskStatus.PENDING

    def test_save_updates_existing_task(self, store: MemoryStore) -> None:
        """Saving a task with same ID updates it."""
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

    def test_get_pending_tasks(self, store: MemoryStore) -> None:
        """Get only pending tasks."""
        store.create("run-1", "Goal", 10)

        store.save_task("run-1", Task(id="task-001", description="Pending 1", status=TaskStatus.PENDING))
        store.save_task("run-1", Task(id="task-002", description="Done", status=TaskStatus.DONE))
        store.save_task("run-1", Task(id="task-003", description="Pending 2", status=TaskStatus.PENDING))

        pending = store.get_pending_tasks("run-1")
        assert len(pending) == 2
        assert all(t.status == TaskStatus.PENDING for t in pending)

    def test_get_pending_ordered_by_priority(self, store: MemoryStore) -> None:
        """Pending tasks are ordered by priority descending."""
        store.create("run-1", "Goal", 10)

        store.save_task("run-1", Task(id="tasklow0", description="Low priority", priority=3))
        store.save_task("run-1", Task(id="taskhigh", description="High priority", priority=9))
        store.save_task("run-1", Task(id="taskmid0", description="Mid priority", priority=5))

        pending = store.get_pending_tasks("run-1")
        assert len(pending) == 3
        assert pending[0].id == "taskhigh"
        assert pending[1].id == "taskmid0"
        assert pending[2].id == "tasklow0"

    def test_get_all_empty(self, store: MemoryStore) -> None:
        """Get all returns empty list when no tasks."""
        store.create("run-1", "Goal", 10)
        tasks = store.get_all_tasks("run-1")
        assert tasks == []


class TestContextStore:
    """Tests for ContextStore protocol implementation."""

    def test_save_and_get_result(self, store: MemoryStore) -> None:
        """Save a result and retrieve it."""
        store.create("run-1", "Goal", 10)

        store.save_result("run-1", "task-1", "Result 1")
        store.save_result("run-1", "task-2", "Result 2")

        context = store.get_all_results("run-1")
        assert context == {"task-1": "Result 1", "task-2": "Result 2"}

    def test_save_result_updates_existing(self, store: MemoryStore) -> None:
        """Saving result with same task_id updates it."""
        store.create("run-1", "Goal", 10)

        store.save_result("run-1", "task-1", "Original")
        store.save_result("run-1", "task-1", "Updated")

        context = store.get_all_results("run-1")
        assert context == {"task-1": "Updated"}

    def test_get_all_results_empty(self, store: MemoryStore) -> None:
        """Get all returns empty dict when no results."""
        store.create("run-1", "Goal", 10)
        context = store.get_all_results("run-1")
        assert context == {}


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_duplicate_run_id_raises(self, store: MemoryStore) -> None:
        """Creating a run with duplicate ID raises KeyError."""
        store.create("run-1", "Goal", 10)

        with pytest.raises(KeyError):
            store.create("run-1", "Different goal", 5)

    def test_get_tasks_nonexistent_run(self, store: MemoryStore) -> None:
        """Getting tasks for non-existent run returns empty list."""
        tasks = store.get_all_tasks("nonexistent")
        assert tasks == []

    def test_get_results_nonexistent_run(self, store: MemoryStore) -> None:
        """Getting results for non-existent run returns empty dict."""
        results = store.get_all_results("nonexistent")
        assert results == {}

    def test_update_loop_state_nonexistent_run(self, store: MemoryStore) -> None:
        """Updating loop state for non-existent run silently does nothing."""
        store.update_loop_state("nonexistent", Phase.EXECUTING, 1, None)
        assert store.get("nonexistent") is None

    def test_save_task_nonexistent_run_raises(self, store: MemoryStore) -> None:
        """Saving task for non-existent run raises KeyError."""
        with pytest.raises(KeyError):
            store.save_task("nonexistent", Task(id="task0001", description="Orphan"))

    def test_save_result_nonexistent_run_raises(self, store: MemoryStore) -> None:
        """Saving result for non-existent run raises KeyError."""
        with pytest.raises(KeyError):
            store.save_result("nonexistent", "task0001", "Orphan result")


class TestIsolation:
    """Tests for run_id isolation."""

    def test_tasks_isolated_by_run_id(self, store: MemoryStore) -> None:
        """Tasks from different runs don't interfere."""
        store.create("run-a", "Goal A", 10)
        store.create("run-b", "Goal B", 10)

        store.save_task("run-a", Task(id="task0001", description="Task for A"))
        store.save_task("run-b", Task(id="task0001", description="Task for B"))

        tasks_a = store.get_all_tasks("run-a")
        tasks_b = store.get_all_tasks("run-b")

        assert len(tasks_a) == 1
        assert len(tasks_b) == 1
        assert tasks_a[0].description == "Task for A"
        assert tasks_b[0].description == "Task for B"

    def test_context_isolated_by_run_id(self, store: MemoryStore) -> None:
        """Context from different runs don't interfere."""
        store.create("run-a", "Goal A", 10)
        store.create("run-b", "Goal B", 10)

        store.save_result("run-a", "task0001", "Result A")
        store.save_result("run-b", "task0001", "Result B")

        context_a = store.get_all_results("run-a")
        context_b = store.get_all_results("run-b")

        assert context_a == {"task0001": "Result A"}
        assert context_b == {"task0001": "Result B"}


class TestRoundTrip:
    """Integration test for full round-trip persistence."""

    def test_full_orchestration_round_trip(self, store: MemoryStore) -> None:
        """Test complete orchestration state persistence."""
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
        tasks[0] = tasks[0].model_copy(update={"status": TaskStatus.DONE, "result": "Research complete"})
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
