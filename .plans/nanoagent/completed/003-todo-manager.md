# Task 003: TodoManager with Unit Tests

**Iteration:** Foundation
**Status:** COMPLETED
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
- [x] todo_manager_test.py has tests for all methods
- [x] Tests cover: empty queue, single task, multiple priorities, mark_done updates, edge cases
- [x] get_next returns highest priority pending task
- [x] Completed tasks are tracked correctly
- [x] `uv run test nanoagent/core/todo_manager_test.py` passes
- [x] `uv run check` passes

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

**implementation:**
- Followed TDD: wrote 15 comprehensive tests covering all functionality first
- Implemented TodoManager with deterministic task queue:
  - `add_tasks()`: Creates tasks with priority (default 5)
  - `get_next()`: Returns highest priority pending task
  - `mark_done()`: Marks task complete and tracks in completed set
  - `get_pending()`: Returns list of pending tasks
  - `get_done()`: Returns list of completed tasks
- Implementation: 56 LOC (within target ~60)
- All 15 TodoManager tests passing (60/60 full suite passing)
- Full test coverage including:
  - Empty queue behavior
  - Single and multiple tasks
  - Priority ordering (highest first)
  - Mark done transitions
  - Edge cases (nonexistent task IDs don't crash)
  - Default priority (5)
- Quality checks passing:
  - ruff lint: All checks passed
  - basedpyright: 0 errors, 0 warnings
  - Full test suite: 60/60 passing
- Working Result verified: ✓ All components implemented and tested

**review:**
Security: 78/100 | Quality: 95/100 | Performance: 95/100 | Tests: 95/100

Working Result verified: ✓ All blocking issues resolved
Validation: 6/6 passing (including CANCELLED status, result storage, error logging)
Full test suite: 63/63 passing (18 TodoManager-specific tests)
Diff: 88 LOC implementation + 202 LOC tests

**Specialized Review Findings:**

Test Coverage: APPROVED ✅
- All 3 blocking issues from previous review resolved with comprehensive tests
- CANCELLED status properly tested and handled
- Result parameter storage validated
- Error logging verified with caplog fixture
- No remaining CRITICAL gaps (0 gaps rated 9-10)

Error Handling: APPROVED ✅
- Silent failures eliminated with structured logging
- mark_done() now logs WARNING for nonexistent task IDs with debugging context
- Result parameter properly stored in Task model
- All previous HIGH severity issues resolved
- Logging implementation follows best practices

Security: APPROVED WITH RECOMMENDATIONS ✅
- Score improved from 72/100 to 78/100 (all CRITICAL issues resolved)
- Cryptographically secure task ID generation ✓
- Comprehensive security test suite validates injection protection ✓
- Structured logging prevents log injection attacks ✓
- HIGH issue (secret exposure in task results): Deferred for production hardening - acceptable for M1 POC
  - Recommendation: Add secret redaction before logging in future milestones
  - Current implementation safe for POC as long as task results don't contain raw secrets
- MODERATE issue (unbounded result size): Deferred per project direction

**implementation (revision 1):**
- ✅ Fixed CANCELLED status handling: test_cancelled_tasks_excluded_from_pending() validates proper filtering
- ✅ Added logging to mark_done(): WARNING level with context (task_id, total_tasks, completed_count)
- ✅ Fixed unused result parameter: Now stored in Task.result field for future reflection
- ✅ Added Task.result field to schemas.py (string | None)
- ✅ Added 3 comprehensive test cases:
  - test_cancelled_tasks_excluded_from_pending: Validates CANCELLED status filtering
  - test_result_stored_in_task: Validates result storage and retrieval
  - test_mark_done_nonexistent_logs_warning: Validates warning logging with caplog
- Implementation: 88 LOC (clean, well-documented)
- Test suite: 18 TodoManager tests, 63/63 full suite passing
- Quality checks: All passing (ruff lint clean, basedpyright 0 errors)
- Working Result verified: ✓ All components implemented, tested, and validated

**testing:**
Validated 18 behavior-focused tests covering all TodoManager functionality

Test breakdown:
- Unit tests: 18 (all passing)
- Integration tests: 0 (not applicable for in-memory queue)
- Total: 18/18 passing

Coverage:
- Statements: 100% (31/31)
- Branches: 100% (all code paths tested)
- Functions: 100% (all methods tested)
- Lines: 100%

All requirements validated:
- ✅ Empty queue handling
- ✅ Priority-based ordering (highest first)
- ✅ Task status transitions (PENDING → DONE)
- ✅ CANCELLED status filtering
- ✅ Result parameter storage
- ✅ Error logging for nonexistent tasks
- ✅ Edge cases (same priority, mark nonexistent)

Full test suite: 63/63 passing (no regressions)
Quality checks: ruff lint clean, basedpyright 0 errors

Working Result verified: ✓ TodoManager fully tested and production-ready for M1

COMPLETED
