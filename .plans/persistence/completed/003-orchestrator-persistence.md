# Task 003: Refactor Orchestrator to use Stores

## Goal

Replace in-memory `context` and `iteration` with `RunStore` + `ContextStore`, adding checkpoint calls at appropriate loop positions.

## Working Result

- `Orchestrator` accepts optional stores and `run_id` in constructor
- When stores provided, creates run record and checkpoints state at each phase transition
- `context` dict is persisted via `ContextStore.save_result()`
- Loop state (`phase`, `iteration`, `current_task_id`) persisted via `RunStore.update_loop_state()`
- All existing Orchestrator tests pass unchanged (16 tests)

## Constraints

- Public API unchanged: `__init__(goal, max_iterations, registry)` signature preserved
- Add optional `run_store`, `task_store`, `context_store`, `run_id` parameters
- Must work with both SQLiteStore and MemoryStore
- Existing tests run without modification (no stores = in-memory mode)
- TDD: Write failing tests first
- Depends on M2 completion (TodoManager uses TaskStore)

## Dependencies

- Task 002 (M2): TodoManager refactor must be complete
- Task 001 (M1): Store protocols and implementations

<guidance>
**Approach: Conditional Store Integration**

Similar to TodoManager, Orchestrator should work in two modes:
1. **Standalone mode** (current): In-memory, no persistence
2. **Persistent mode** (new): Uses stores for all state

**Constructor changes:**
```python
def __init__(
    self,
    goal: str,
    max_iterations: int = 10,
    registry: ToolRegistry | None = None,
    # New optional parameters for persistence
    run_store: RunStore | None = None,
    task_store: TaskStore | None = None,
    context_store: ContextStore | None = None,
    run_id: str | None = None,
) -> None:
```

**Validation rules:**
- If any store is provided, ALL stores must be provided (or raise ValueError)
- If stores provided, `run_id` must also be provided
- Create run record in `run_store` during `__init__`

**Checkpoint positions in the loop:**

1. **After planning** (Phase.PLANNING → Phase.EXECUTING):
   ```python
   # In run(), after plan_tasks() returns:
   self.todo.add_tasks(plan_output.tasks)
   if self._run_store:
       self._run_store.update_loop_state(
           self._run_id, Phase.EXECUTING, 0, None
       )
   ```

2. **Before executing task** (update current_task_id):
   ```python
   # In _iteration_step(), before execute_task():
   if self._run_store:
       self._run_store.update_loop_state(
           self._run_id, Phase.EXECUTING, self.iteration, current_task.id
       )
   ```

3. **After task completion** (save result):
   ```python
   # After marking task done:
   if self._context_store:
       self._context_store.save_result(self._run_id, task_id, result)
   ```

4. **Before reflection**:
   ```python
   if self._run_store:
       self._run_store.update_loop_state(
           self._run_id, Phase.REFLECTING, self.iteration, None
       )
   ```

5. **On completion** (Phase.DONE):
   ```python
   if self._run_store:
       self._run_store.update_loop_state(
           self._run_id, Phase.DONE, self.iteration, None
       )
   ```

**Context persistence:**
- Replace `self.context[task_id] = result` with `self._context_store.save_result()`
- When reading context for synthesis, use `self._context_store.get_all_results()` if store exists

**TodoManager integration:**
- After M2, TodoManager can accept a TaskStore
- Pass `task_store` and `run_id` to TodoManager when creating it

**Tests to add:**
- Checkpoint test: verify `update_loop_state` called at correct positions
- Context persistence: results saved via `save_result()`
- All-or-nothing stores validation
- Works with MemoryStore (fast tests)
- Works with SQLiteStore (integration test)
</guidance>

## Validation

- [x] Existing Orchestrator tests pass unchanged (16 tests)
- [x] Constructor validates all-or-nothing store injection
- [x] Run record created on init when stores provided
- [x] Checkpoint at Phase.EXECUTING after planning
- [x] Checkpoint before each task execution (with task_id)
- [x] Context saved via ContextStore after each task
- [x] Checkpoint at Phase.REFLECTING before reflection
- [x] Checkpoint at Phase.DONE on completion
- [x] Works with MemoryStore
- [x] Works with SQLiteStore
- [x] basedpyright passes
- [x] ruff passes

**Status:** APPROVED

**implementation:**
- Added optional `run_store`, `task_store`, `context_store`, `run_id` parameters to `Orchestrator.__init__()`
- Constructor validates all-or-nothing store injection (if any store provided, all must be provided)
- Run record created via `run_store.create()` during init when stores provided
- TodoManager passed `task_store` and `run_id` when stores provided
- Checkpoint at EXECUTING after planning via `run_store.update_loop_state()`
- Checkpoint before each task execution with `current_task_id`
- Context saved via `context_store.save_result()` after each task execution
- Checkpoint at REFLECTING before reflection
- Checkpoint at DONE on completion (both via reflection.done and max iterations)
- 12 new tests covering all persistence scenarios
- Full test suite: 307/307 passing (was 295)
- Existing 16 Orchestrator tests pass unchanged (backward compatibility preserved)
- Working Result verified: ✓ Orchestrator checkpoints state at each phase transition
- Files:
  - `nanoagent/core/orchestrator.py` - Added persistence mode with checkpoint calls
  - `nanoagent/core/orchestrator_test.py` - Added 12 persistence tests

**testing:**
Validated 31 tests (all behavior-focused, no mocking of store calls)

Added 2 edge cases:
- test_checkpoint_at_done_via_max_iterations: Verifies DONE phase on max iterations termination
- test_context_saved_for_failed_execution: Verifies context saved even for failed task execution

Test breakdown: Unit: 3 (validation) | Integration: 28 (orchestration flows) | Total: 31
Full suite: 309/309 passing
Working Result verified: ✓ Orchestrator checkpoints state at each phase transition with full test coverage

**review:**
Security: 90/100 | Quality: 90/100 | Performance: 95/100 | Tests: 85/100

Working Result verified: ✓ Orchestrator checkpoints state at each phase transition
Validation: 12/12 items passing
Full test suite: 309/309 passing
Diff: 523 lines (70 impl + 453 tests)

**Specialized Review Findings:**

- Test Coverage: No CRITICAL gaps (0 gaps rated 9-10). Store failure modes flagged at 8/10 but follow approved error propagation pattern from Task 001.
- Error Handling: No CRITICAL issues. Store operations propagate errors to caller (intentional design - follows Task 001/002 pattern). Adding try-catch would only log + re-raise.
- Security: No vulnerabilities detected (0 findings >70 confidence). Parameterized queries, cryptographic task IDs, input validation present. run_id validation flagged at 62 confidence (defense-in-depth suggestion, not blocking).

HIGH findings (acceptable with justification):
1. [Test] Store failure modes not explicitly tested - Criticality 8/10. Store implementations already tested in Task 001. Errors propagate to caller by design. This is consistent with "promise theory" pattern approved in prior tasks.
2. [Error] Store operations without explicit try-catch - HIGH. Intentional: errors propagate to Orchestrator caller who handles failures. Consistent with Task 001/002 design.

APPROVED → completed
