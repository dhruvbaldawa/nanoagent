# Task 004: Implement Orchestrator Resume

## Goal

Add `Orchestrator.resume(run_id)` class method to continue an interrupted orchestration from its last checkpoint.

## Working Result

- `Orchestrator.resume(run_id, stores)` class method creates Orchestrator from persisted state
- Resume reconstructs full state: goal, iteration, tasks, context
- Resume continues from checkpoint position (re-executes task if crashed mid-execution)
- Resumed orchestration completes successfully

## Constraints

- New API surface: `Orchestrator.resume()` class method
- Must handle all checkpoint positions: planning, executing (with task_id), reflecting, done
- If checkpoint was mid-task (current_task_id set), re-execute that task
- TDD: Write failing tests first
- Depends on Task 003 (checkpointing)

## Dependencies

- Task 003: Orchestrator persistence/checkpointing
- Task 002: TodoManager refactor
- Task 001: Store protocols

<guidance>
**Resume API Design:**

```python
@classmethod
async def resume(
    cls,
    run_id: str,
    run_store: RunStore,
    task_store: TaskStore,
    context_store: ContextStore,
    registry: ToolRegistry | None = None,
) -> "Orchestrator":
    """
    Resume an orchestration from its last checkpoint.

    Args:
        run_id: ID of the run to resume
        run_store, task_store, context_store: Store implementations
        registry: Optional ToolRegistry (creates new if not provided)

    Returns:
        Orchestrator instance ready to continue via run()

    Raises:
        ValueError: If run_id not found
    """
```

**Resume Logic:**

1. **Load run state:**
   ```python
   run_state = run_store.get(run_id)
   if run_state is None:
       raise ValueError(f"Run not found: {run_id}")
   ```

2. **Create orchestrator with loaded state:**
   ```python
   orchestrator = cls(
       goal=run_state.goal,
       max_iterations=run_state.max_iterations,
       registry=registry,
       run_store=run_store,
       task_store=task_store,
       context_store=context_store,
       run_id=run_id,
   )
   orchestrator.iteration = run_state.iteration
   ```

3. **Reconstruct context:**
   ```python
   orchestrator.context = context_store.get_all_results(run_id)
   ```

4. **Handle checkpoint position:**
   The `run()` method needs modification to handle resume:

   - If `phase == Phase.DONE`: Return immediately (already complete)
   - If `phase == Phase.PLANNING`: Start from beginning (rare - crash during planning)
   - If `phase == Phase.EXECUTING`:
     - If `current_task_id` is set: Re-execute that specific task
     - Otherwise: Continue with next pending task
   - If `phase == Phase.REFLECTING`: Jump to reflection

**Key insight from M1 POC:**
The checkpoint is saved BEFORE LLM execution. So on resume:
- If we crashed during task execution, re-execute the task (idempotent)
- If we crashed after task completion but before next checkpoint, we re-execute (acceptable)

**Modifying run() for resume:**

Option A: Add `_resumed_phase` flag checked in `run()`
Option B: Separate `_resume_run()` method that joins the loop at correct position

Recommend Option B for clarity - `run()` calls `_resume_run()` if phase != PLANNING.

**Tests to add:**
- Resume from Phase.EXECUTING (no current_task): picks up next task
- Resume from Phase.EXECUTING (with current_task_id): re-executes that task
- Resume from Phase.REFLECTING: goes straight to reflection
- Resume from Phase.DONE: returns immediately
- Resume preserves context (completed tasks visible)
- Resume with SQLiteStore (integration)
- ValueError on non-existent run_id
</guidance>

## Validation

- [ ] `Orchestrator.resume()` class method exists
- [ ] Resume loads goal, max_iterations, iteration from RunStore
- [ ] Resume loads context from ContextStore
- [ ] Resume from Phase.EXECUTING continues with pending tasks
- [ ] Resume with current_task_id re-executes that task
- [ ] Resume from Phase.REFLECTING triggers reflection immediately
- [ ] Resume from Phase.DONE returns completed result
- [ ] Resumed orchestration can complete successfully
- [ ] ValueError raised for non-existent run_id
- [ ] Works with MemoryStore
- [ ] Works with SQLiteStore
- [ ] basedpyright passes
- [ ] ruff passes
