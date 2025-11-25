# Task 003: Convert task_planner_test.py to use TestModel

## Objective
Convert remaining tests in `task_planner_test.py` that use `require_real_api_key` fixture to use `TestModel + Agent.override()`.

## Context
- File: `nanoagent/core/task_planner_test.py`
- Current state: Some tests already use TestModel (lines 163-178), but class still has `@pytest.mark.usefixtures("require_real_api_key")`
- Target state: All tests use `TestModel` consistently, remove class-level fixture
- Note: Pattern already established in this file - follow existing style

## Implementation

### Existing Pattern (already in file)
```python
from pydantic_ai.models.test import TestModel
from nanoagent.core.task_planner import plan_tasks, task_planner

async def test_valid_goal_returns_structured_output(self) -> None:
    with task_planner.override(model=TestModel()):
        result = await plan_tasks("Build a web application")
        assert isinstance(result, TaskPlanOutput)
```

### Steps
1. Remove `@pytest.mark.usefixtures("require_real_api_key")` from class
2. Ensure all tests that call `plan_tasks()` use the TestModel override
3. Follow the existing pattern in lines 163-178
4. Verify all tests pass with `pytest nanoagent/core/task_planner_test.py -v`

## LLM Prompt

```
Review and update nanoagent/core/task_planner_test.py to ensure all tests use TestModel.

Reference: Lines 163-178 already show the correct pattern:
- Import TestModel from pydantic_ai.models.test
- Use: with task_planner.override(model=TestModel()):

Tasks:
1. Remove @pytest.mark.usefixtures("require_real_api_key") from class level
2. Ensure any remaining tests that make API calls are converted to use TestModel
3. Maintain consistency with existing TestModel usage pattern in the file
```

## Success Criteria
- [ ] `require_real_api_key` fixture removed from task_planner_test.py
- [ ] All tests use `TestModel` override consistently
- [ ] `pytest nanoagent/core/task_planner_test.py -v` passes in <1s
- [ ] No API calls made during test execution

## Files
- `nanoagent/core/task_planner_test.py` (modify)

## Estimated LOC: ~10
