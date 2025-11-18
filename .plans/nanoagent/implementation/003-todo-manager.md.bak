# Task 003: TodoManager with Unit Tests

**Iteration:** Foundation
**Status:** Pending
**Dependencies:** 002
**Files:** nanoagent/core/todo_manager.py, nanoagent/core/todo_manager_test.py

## Description
Implement TodoManager as a plain Python class for task queue management. Follow TDD: write tests for each method first, then implement. Target ~60 LOC for implementation.

## Working Result
- TodoManager class with task storage (Dict[str, Task]) and completed set (Set[str])
- Methods: add_tasks, get_next, mark_done, get_pending, get_done
- Priority-based task selection working correctly
- Comprehensive unit tests covering all methods and edge cases
- All tests passing

## Validation
- [ ] todo_manager_test.py has tests for all methods
- [ ] Tests cover: empty queue, single task, multiple priorities, mark_done updates, edge cases
- [ ] get_next returns highest priority pending task
- [ ] Completed tasks are tracked correctly
- [ ] `uv run test nanoagent/core/todo_manager_test.py` passes
- [ ] `uv run check` passes

## LLM Prompt
<prompt>
**Goal:** Implement deterministic task queue that prioritizes tasks and tracks completion state

**Constraints:**
- Plain Python class (no LLM calls)
- Must follow TDD: write tests before implementation
- Target ~60 LOC for implementation
- Priority-based ordering (highest priority first)
- Track both task state (pending/done) and completion set
- Handle edge cases gracefully (empty queue, nonexistent tasks)

**Required Methods:**
- `add_tasks(descriptions: List[str], priority: int = 5)` - Create tasks with priority
- `get_next() -> Optional[Task]` - Return highest priority pending task
- `mark_done(task_id: str, result: str)` - Mark task complete
- `get_pending() -> List[Task]` - Get all pending tasks
- `get_done() -> List[Task]` - Get all completed tasks

**Implementation Guidance:**
- Store tasks in Dict[str, Task] keyed by task ID
- Maintain separate Set[str] for completed task IDs
- Use Task model from schemas.py
- get_next should filter pending, sort by priority (highest first)
- mark_done should update task status and add to completed set
- Handle nonexistent task IDs gracefully (no crash)
- Add ABOUTME comments

**Test Coverage Required:**
- Empty manager returns None for get_next
- Tasks sorted by priority correctly
- mark_done transitions task to "done" status
- Completed set tracks finished task IDs
- get_pending excludes done/cancelled tasks
- Multiple tasks at same priority handled
- Edge case: marking nonexistent task doesn't crash

**Validation:**
- All tests in todo_manager_test.py pass
- Implementation ~60 LOC
- Run `uv run check` - no errors
</prompt>

## Notes

**planning:** TodoManager is pure logic, no LLM calls - perfect for TDD. This proves the task queue works before adding agent complexity. Keep implementation simple and deterministic. Target ~60 LOC.
