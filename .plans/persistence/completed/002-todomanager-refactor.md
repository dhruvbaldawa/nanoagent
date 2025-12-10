# Task 002: Refactor TodoManager to use TaskStore

## Goal

Replace in-memory storage with TaskStore dependency while maintaining backward compatibility for existing tests.

## Working Result

- `TodoManager` accepts optional `TaskStore` and `run_id` in constructor
- When store is provided, all operations delegate to store
- When store is None (default), uses in-memory storage (current behavior)
- All existing TodoManager tests pass unchanged
- New tests verify persistence mode works correctly

## Constraints

- Public API unchanged: `add_tasks`, `get_next`, `mark_done`, `get_pending`, `get_done`
- Must work with both `SQLiteStore` and `MemoryStore`
- Existing tests run without modification (no store = in-memory mode)
- TDD: Write failing tests first

## Dependencies

- Task 001 (completed): Store protocols and implementations

<guidance>
**Approach: Conditional Delegation**

The key insight is that TodoManager should work in two modes:

1. **Standalone mode** (current): In-memory storage, no persistence
2. **Persistent mode** (new): Delegates to TaskStore

Constructor signature change:

```python
def __init__(
    self,
    store: TaskStore | None = None,
    run_id: str | None = None,
) -> None:
```

**Implementation considerations:**

1. **Validation**: If `store` is provided, `run_id` must also be provided (and vice versa). Raise `ValueError` otherwise.

2. **Method delegation**: Each method checks if `self._store` exists:
   - `add_tasks`: Create Task objects, save via `store.save_task()`, return IDs
   - `get_next`: Use `store.get_pending_tasks()`, sort by priority, return first
   - `mark_done`: Update task status, call `store.save_task()` to persist
   - `get_pending`: Return `store.get_pending_tasks()`
   - `get_done`: Filter `store.get_all_tasks()` by status

3. **Task result storage**: Current TodoManager stores `result` on the Task object. The TaskStore protocol's `save_task` already handles this since Task has a `result` field.

4. **Existing tests**: These don't pass a store, so they use in-memory mode and should pass without changes.

5. **New tests to add**:
   - Test with MemoryStore: add tasks → persist → get back
   - Test with SQLiteStore: same
   - Test that changes persist across TodoManager instances (same run_id)
   - Test validation: store without run_id raises error

**Watch out for:**

- The `completed` set is redundant when using store (status is on Task)
- Priority ordering must match between in-memory and persistent mode
</guidance>

## Validation

- [x] Existing TodoManager tests pass unchanged (12 tests)
- [x] Constructor validates store/run_id consistency
- [x] `add_tasks` persists to store when provided
- [x] `get_next` returns highest priority pending task from store
- [x] `mark_done` updates task status in store
- [x] `get_pending` reads from store
- [x] `get_done` reads from store
- [x] Tasks persist across TodoManager instances (same store + run_id)
- [x] Works with both MemoryStore and SQLiteStore
- [x] basedpyright passes
- [x] ruff passes

**Status:** APPROVED

**implementation:**

- Added optional `store: TaskStore` and `run_id: str` parameters to `TodoManager.__init__()`
- Constructor validates store/run_id consistency (both required together)
- All methods (add_tasks, get_next, mark_done, get_pending, get_done) check `self._store` and delegate when present
- 11 new tests covering: validation, persistence, cross-instance persistence, SQLiteStore integration
- Full test suite: 293/293 passing (was 282)
- Existing 18 TodoManager tests pass unchanged (backward compatibility preserved)
- Working Result verified: ✓ TodoManager works in both standalone and persistent modes
- Files:
  - `nanoagent/core/todo_manager.py` - Added persistence mode with conditional delegation
  - `nanoagent/core/todo_manager_test.py` - Added 11 persistence tests

**testing:**
Validated 31 tests (all behavior-focused, no mocking)

Added 2 edge cases:

- test_mark_done_nonexistent_in_persistent_mode: Error handling in persistent mode
- test_empty_store_returns_none: Empty store boundary condition

Test breakdown: Unit: 18 (standalone) | Integration: 13 (persistent) | Total: 31
Full suite: 295/295 passing
Working Result verified: ✓ TodoManager supports both in-memory and persistent modes with full test coverage

**review:**
Security: 95/100 | Quality: 90/100 | Performance: 95/100 | Tests: 90/100

Working Result verified: ✓ TodoManager supports both standalone and persistent modes
Validation: 11/11 items passing
Full test suite: 295/295 passing
Diff: 334 lines

**Specialized Review Findings:**

- Test Coverage: No CRITICAL gaps after context review. Concurrent operations tested at store layer (SQLiteStore). TodoManager delegates to store protocols. (0 gaps rated 9-10 blocking)
- Error Handling: Store operations propagate errors to caller (intentional - follows "promise theory" pattern approved in Task 001). No silent failures. (0 CRITICAL after context)
- Security: No vulnerabilities detected (0 findings >50 confidence). Parameterized queries, cryptographic task IDs, proper input validation.

HIGH findings (acceptable with justification):

1. [Error] Store exception handling - Errors propagate to caller. This is intentional design: caller (Orchestrator) handles failures. Adding try-catch would only log + re-raise. Pattern consistent with Task 001 approval.

APPROVED → completed
