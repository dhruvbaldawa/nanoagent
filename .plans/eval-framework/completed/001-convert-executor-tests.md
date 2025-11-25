# Task 001: Convert executor_test.py to use TestModel

## Objective
Convert all tests in `executor_test.py` that use `require_real_api_key` fixture to use `TestModel + Agent.override()` for fast, deterministic execution.

## Context
- File: `nanoagent/core/executor_test.py`
- Current state: Uses `@pytest.mark.usefixtures("require_real_api_key")` at class level
- Target state: Each test uses `with executor.override(model=TestModel()):`

## Implementation

### Pattern
```python
from pydantic_ai.models.test import TestModel
from nanoagent.core.executor import executor

async def test_executor_structured_output(self):
    with executor.override(model=TestModel()):
        result = await execute_task("test task")
        assert isinstance(result, ExecutionResult)
```

### Steps
1. Remove `@pytest.mark.usefixtures("require_real_api_key")` from class
2. Import `TestModel` from `pydantic_ai.models.test`
3. Wrap each async test body with `with executor.override(model=TestModel()):`
4. Verify all tests pass with `pytest nanoagent/core/executor_test.py -v`

## LLM Prompt

```
Convert the tests in nanoagent/core/executor_test.py to use TestModel instead of real API calls.

Current pattern to replace:
- Class has @pytest.mark.usefixtures("require_real_api_key")
- Tests make real LLM API calls

New pattern to use:
- Remove require_real_api_key fixture
- Wrap test body with: with executor.override(model=TestModel()):
- Import: from pydantic_ai.models.test import TestModel

Ensure all assertions still validate the expected behavior (schema validation, output types).
```

## Success Criteria
- [ ] `require_real_api_key` fixture removed from executor_test.py
- [ ] All tests use `TestModel` override
- [ ] `pytest nanoagent/core/executor_test.py -v` passes in <1s
- [ ] No API calls made during test execution

## Files
- `nanoagent/core/executor_test.py` (modify)

## Estimated LOC: ~10

**Status:** APPROVED

## Working Result
- ✅ Removed `@pytest.mark.usefixtures("require_real_api_key")` from TestExecutor class
- ✅ Added `from pydantic_ai.models.test import TestModel` import
- ✅ Wrapped all 4 test methods with `with test_executor.override(model=TestModel()):`
- ✅ All tests pass in <1s with deterministic behavior (4 passed in 0.25s)
- ✅ No API calls made during test execution

## Implementation Details
- Modified 4 test methods in TestExecutor class to use TestModel override pattern
- Pattern: Create agent instance, then wrap agent.run() call with `with agent.override(model=TestModel()):`
- Tests validated: all assertions passing, correct data types returned
- No changes needed to TestExecuteTaskFunction class (already mocked correctly)

**review:**
Security: 95/100 | Quality: 95/100 | Performance: 98/100 | Tests: 98/100

Working Result verified: ✓ All 4 TestExecutor methods use TestModel override, all 13 TestExecuteTaskFunction tests use mocks
Validation: 4/4 success criteria passing
Full test suite: 17/17 passing (executor_test.py in 0.27s)
Diff: ~55 lines changed

**Specialized Review Findings:**
- Test Coverage: No gaps - tests cover success/failure paths, structured output validation, error handling
- Error Handling: All exceptions properly caught and re-raised with context preservation
- Security: No vulnerabilities detected - input validation in place, no API key exposure

APPROVED
