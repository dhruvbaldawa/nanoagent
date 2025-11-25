# Task 004: Convert e2e_test.py to use TestModel

## Objective
Convert all tests in `e2e_test.py` that use `require_real_api_key` fixture to use `TestModel + Agent.override()` for fast, deterministic execution.

## Context
- File: `nanoagent/tests/integration/e2e_test.py`
- Current state: Uses `@pytest.mark.usefixtures("require_real_api_key")` at class level
- Target state: All agents (task_planner, executor, reflector) use TestModel override
- Note: E2E tests may need to override multiple agents

## Implementation

### Pattern for Multiple Agents
```python
from pydantic_ai.models.test import TestModel
from nanoagent.core.task_planner import task_planner
from nanoagent.core.executor import executor
from nanoagent.core.reflector import reflector

async def test_full_orchestration(self):
    with task_planner.override(model=TestModel()), \
         executor.override(model=TestModel()), \
         reflector.override(model=TestModel()):
        # Test orchestration flow
        result = await orchestrate_task("Build a web app")
        assert result is not None
```

### Steps
1. Remove `@pytest.mark.usefixtures("require_real_api_key")` from class
2. Import `TestModel` and all agent instances
3. Wrap each test with multiple agent overrides as needed
4. Verify all tests pass with `pytest nanoagent/tests/integration/e2e_test.py -v`

## LLM Prompt

```
Convert the e2e tests in nanoagent/tests/integration/e2e_test.py to use TestModel instead of real API calls.

Key consideration: E2E tests involve multiple agents (task_planner, executor, reflector).
Each agent that makes LLM calls needs its own TestModel override.

Pattern for multiple agents:
with task_planner.override(model=TestModel()), \
     executor.override(model=TestModel()), \
     reflector.override(model=TestModel()):
    # test code

Steps:
1. Remove @pytest.mark.usefixtures("require_real_api_key")
2. Import TestModel and agent instances
3. Override all agents used in each test
4. Ensure assertions validate the orchestration flow
```

## Success Criteria
- [ ] `require_real_api_key` fixture removed from e2e_test.py
- [ ] All 6 tests use `TestModel` overrides for all agents
- [ ] `pytest nanoagent/tests/integration/e2e_test.py -v` passes in <1s
- [ ] No API calls made during test execution

## Files
- `nanoagent/tests/integration/e2e_test.py` (modify)

## Estimated LOC: ~10
