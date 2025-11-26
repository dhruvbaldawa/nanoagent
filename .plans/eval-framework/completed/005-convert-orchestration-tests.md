# Task 005: Convert orchestration_test.py to use TestModel

## Objective
Convert all tests in `orchestration_test.py` that use `require_real_api_key` fixture to use `TestModel + Agent.override()` for fast, deterministic execution.

## Context
- File: `nanoagent/tests/integration/orchestration_test.py`
- Current state: Uses `@pytest.mark.usefixtures("require_real_api_key")` at class level
- Target state: All agents use TestModel override
- Note: 2 tests in this file

## Implementation

### Pattern
```python
from pydantic_ai.models.test import TestModel
from nanoagent.core.task_planner import task_planner
from nanoagent.core.executor import executor
from nanoagent.core.reflector import reflector

async def test_orchestration(self):
    with task_planner.override(model=TestModel()), \
         executor.override(model=TestModel()), \
         reflector.override(model=TestModel()):
        # Test orchestration flow
        ...
```

### Steps
1. Remove `@pytest.mark.usefixtures("require_real_api_key")` from class
2. Import `TestModel` and agent instances
3. Wrap each test with appropriate agent overrides
4. Verify all tests pass with `pytest nanoagent/tests/integration/orchestration_test.py -v`

## LLM Prompt

```
Convert the tests in nanoagent/tests/integration/orchestration_test.py to use TestModel instead of real API calls.

Similar to e2e_test.py, orchestration tests may involve multiple agents.
Override each agent used in the test with TestModel.

Pattern:
with task_planner.override(model=TestModel()), \
     executor.override(model=TestModel()), \
     reflector.override(model=TestModel()):
    # test code

Steps:
1. Remove @pytest.mark.usefixtures("require_real_api_key")
2. Import TestModel and relevant agent instances
3. Override agents as needed in each test
```

## Success Criteria
- [x] `require_real_api_key` fixture removed from orchestration_test.py
- [x] All 2 tests use `TestModel` overrides
- [x] `pytest nanoagent/tests/integration/orchestration_test.py -v` passes in <1s
- [x] No API calls made during test execution

**Status:** APPROVED

## Working Result
- ✅ All 2 orchestration tests converted
- ✅ Tests pass in <0.25s
- ✅ Full suite: 202/202 tests passing

**review:** APPROVED

## Files
- `nanoagent/tests/integration/orchestration_test.py` (modify)

## Estimated LOC: ~5
