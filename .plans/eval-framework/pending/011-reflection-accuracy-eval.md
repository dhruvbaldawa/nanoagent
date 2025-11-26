# Task 011: Create reflection accuracy eval tests

## Goal
Create eval tests for Reflector gap detection and done flag accuracy.

## Context
- File: `nanoagent/tests/evals/reflection_accuracy_eval.py`
- Follows pattern established in task 010
- Tests whether reflector correctly identifies gaps and completion

## Constraints
- Tests marked with `@pytest.mark.eval`
- Uses real LLM calls
- 2 test cases for reflection accuracy dimension

## Test Cases
1. **Complete goal** - Reflector should mark as done=True
2. **Incomplete goal** - Reflector should identify gaps, done=False

## Guidance
- Build Task lists from case data using Task/TaskStatus from schemas
- Call reflect_on_progress(goal, completed, pending)
- Evaluate done flag accuracy and gap identification quality

## Validation
- [ ] `pytest -m eval nanoagent/tests/evals/reflection_accuracy_eval.py -v` runs
- [ ] At least 1/2 cases pass (score >= 3)

## Files
- `nanoagent/tests/evals/cases.py` (add REFLECTION_ACCURACY_CASES)
- `nanoagent/tests/evals/reflection_accuracy_eval.py` (create)
