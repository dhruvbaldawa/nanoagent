# Task 012: Create execution correctness eval tests

## Goal
Create eval tests for Executor success flag accuracy and output quality.

## Context
- File: `nanoagent/tests/evals/execution_correctness_eval.py`
- Follows pattern established in task 010
- Tests whether executor correctly reports success/failure

## Constraints
- Tests marked with `@pytest.mark.eval`
- Uses real LLM calls
- 2 test cases for execution correctness dimension

## Test Cases
1. **Successful task** - Task with tools should return success=True
2. **Impossible task** - Task without tools should return success=False

## Guidance
- Call execute_task(task, available_tools)
- Evaluate success flag accuracy and output detail

## Validation
- [ ] `pytest -m eval nanoagent/tests/evals/execution_correctness_eval.py -v` runs
- [ ] At least 1/2 cases pass (score >= 3)

## Files
- `nanoagent/tests/evals/cases.py` (add EXECUTION_CORRECTNESS_CASES)
- `nanoagent/tests/evals/execution_correctness_eval.py` (create)

**Status:** READY_FOR_REVIEW

## Implementation

- Created execution_correctness_eval.py with 3 parametrized test cases
- Calls execute_task() with task descriptions from EXECUTION_CORRECTNESS_CASES
- Evaluates execution success flag accuracy and output quality using LLM judge
- All 3/3 cases passing (exceeds 1/2 requirement)
- Full test suite: 232/232 passing, no regressions
- Linting and type checks passing
