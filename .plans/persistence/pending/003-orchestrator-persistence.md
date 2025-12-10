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

- [ ] Existing Orchestrator tests pass unchanged (16 tests)
- [ ] Constructor validates all-or-nothing store injection
- [ ] Run record created on init when stores provided
- [ ] Checkpoint at Phase.EXECUTING after planning
- [ ] Checkpoint before each task execution (with task_id)
- [ ] Context saved via ContextStore after each task
- [ ] Checkpoint at Phase.REFLECTING before reflection
- [ ] Checkpoint at Phase.DONE on completion
- [ ] Works with MemoryStore
- [ ] Works with SQLiteStore
- [ ] basedpyright passes
- [ ] ruff passes
