# Task 002: Convert reflector_test.py to use TestModel

## Objective
Convert all tests in `reflector_test.py` that use `require_real_api_key` fixture to use `TestModel + Agent.override()` for fast, deterministic execution.

## Context
- File: `nanoagent/core/reflector_test.py`
- Current state: Uses `@pytest.mark.usefixtures("require_real_api_key")` at class level
- Target state: Each test uses `with reflector.override(model=TestModel()):`
- Note: 7 tests in this file

## Implementation

### Pattern
```python
from pydantic_ai.models.test import TestModel
from nanoagent.core.reflector import reflector

async def test_reflector_structured_output(self):
    with reflector.override(model=TestModel()):
        result = await reflect_on_execution(context)
        assert isinstance(result, ReflectionOutput)
```

### Steps
1. Remove `@pytest.mark.usefixtures("require_real_api_key")` from class
2. Import `TestModel` from `pydantic_ai.models.test`
3. Wrap each async test body with `with reflector.override(model=TestModel()):`
4. Verify all tests pass with `pytest nanoagent/core/reflector_test.py -v`

## LLM Prompt

```
Convert the tests in nanoagent/core/reflector_test.py to use TestModel instead of real API calls.

Current pattern to replace:
- Class has @pytest.mark.usefixtures("require_real_api_key")
- Tests make real LLM API calls

New pattern to use:
- Remove require_real_api_key fixture
- Wrap test body with: with reflector.override(model=TestModel()):
- Import: from pydantic_ai.models.test import TestModel

Ensure all assertions still validate the expected behavior (schema validation, output types).
```

## Success Criteria
- [ ] `require_real_api_key` fixture removed from reflector_test.py
- [ ] All 7 tests use `TestModel` override
- [ ] `pytest nanoagent/core/reflector_test.py -v` passes in <1s
- [ ] No API calls made during test execution

## Files
- `nanoagent/core/reflector_test.py` (modify)

## Estimated LOC: ~15
