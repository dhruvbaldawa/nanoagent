# Task 013: Create convergence eval tests

## Goal
Create eval tests for Orchestrator iteration efficiency and completion detection.

## Context
- File: `nanoagent/tests/evals/convergence_eval.py`
- Follows pattern established in task 010
- Tests full orchestration loop behavior

## Constraints
- Tests marked with `@pytest.mark.eval`
- Uses real LLM calls (full orchestration)
- 2 test cases for convergence dimension

## Test Cases
1. **Simple goal** - Should converge in 1-3 iterations
2. **Multi-step goal** - Should refine without infinite loops

## Guidance
- Create Orchestrator with goal and max_iterations
- Register builtin tools
- Run orchestrator.run()
- Evaluate iteration count, task duplication, output coherence

## Validation
- [ ] `pytest -m eval nanoagent/tests/evals/convergence_eval.py -v` runs
- [ ] At least 1/2 cases pass (score >= 3)

## Files
- `nanoagent/tests/evals/cases.py` (add CONVERGENCE_CASES)
- `nanoagent/tests/evals/convergence_eval.py` (create)
