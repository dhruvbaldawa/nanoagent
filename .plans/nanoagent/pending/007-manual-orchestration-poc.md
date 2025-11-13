# Task 007: Manual Orchestration POC with Integration Test

**Iteration:** Foundation
**Status:** Pending
**Dependencies:** 003, 004, 005, 006
**Files:** nanoagent/core/__init__.py, nanoagent/core/integration_test.py

## Description
Create a proof-of-concept that manually orchestrates one complete cycle: planning → execute 2 tasks → reflection. Write integration test first that validates all components work together. This proves all Critical Risks are manageable.

## Working Result
- Integration test orchestrates complete workflow manually
- Test validates: TaskPlanner → TodoManager → Executor → Reflector flow
- All agents produce correct structured outputs
- Context passing between agents works
- Test proves end-to-end viability before building Orchestrator
- All tests passing

## Validation
- [ ] integration_test.py manually orchestrates complete cycle
- [ ] Test calls TaskPlanner → gets tasks
- [ ] Test adds tasks to TodoManager
- [ ] Test executes 2 tasks with Executor
- [ ] Test calls Reflector with results
- [ ] All structured outputs parse correctly
- [ ] `uv run test nanoagent/core/integration_test.py` passes
- [ ] `uv run check` passes

## LLM Prompt
<prompt>
**Goal:** Prove all foundation components work together end-to-end, validating all Critical Risks are manageable (MILESTONE 1 VALIDATION)

**Constraints:**
- Must manually coordinate all components (no automated orchestration yet)
- Must use real LLM calls throughout
- Must validate context flows correctly between agents
- Must prove structured outputs work at every stage
- Must demonstrate complete cycle: plan → execute → reflect
- Execute at least 2 tasks to prove iteration works

**Implementation Guidance:**
- Write integration test first that coordinates manually
- Use mock tool (e.g., mock_calculator) for executor
- Test flow:
  1. Call task_planner with goal → get TaskPlanOutput
  2. Add tasks to TodoManager
  3. Loop: get_next task, call executor with task, mark_done (2 iterations)
  4. Build context dict with task results
  5. Call reflector with goal, completed tasks, pending tasks
- Validate all structured outputs parse correctly
- Create __init__.py to export core components
- Add ABOUTME comments
- Optional: Add second test validating context preservation

**Critical Validations:**
- **Risk #1**: All structured outputs (TaskPlanOutput, ExecutionResult, ReflectionOutput) parse correctly
- **Risk #2**: Context (task descriptions + results) flows through all phases
- **Risk #3**: Reflection produces sensible done/gaps/new_tasks output

**Mock Tool Example:**
```python
async def mock_calculator(ctx, expression: str) -> str:
    try:
        result = eval(expression)  # Safe for testing
        return f"Result: {result}"
    except Exception as e:
        return f"Error: {str(e)}"
```

**Context Building Pattern:**
```python
context = {}
for _ in range(2):  # Execute 2 tasks
    task = todo.get_next()
    result = await executor.run(task.description, deps=...)
    context[task.id] = result.data.output
    todo.mark_done(task.id, result.data.output)
```

**Validation:**
- Integration test passes (all components coordinate successfully)
- All Critical Risks validated (structured outputs, context passing, reflection quality)
- If this test passes: proceed to Milestone 2
- If this test fails: architecture needs revision
- Run `uv run check` - no errors
</prompt>

## Notes

**planning:** CRITICAL MILESTONE VALIDATION. If this test passes, we've proven the entire foundation works. This is the decision point: proceed to Milestone 2 or adjust architecture if integration fails. All three Critical Risks must be validated here.
