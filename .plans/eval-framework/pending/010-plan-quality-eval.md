# Task 010: Create plan quality eval tests

## Goal
Create first eval test to validate judge works with real LLM calls.

## Context
- Files: `nanoagent/tests/evals/cases.py`, `nanoagent/tests/evals/plan_quality_eval.py`
- **Risk validation**: First real test of LLM-as-judge with actual API calls
- If this works, remaining eval tests follow same pattern

## Constraints
- Tests marked with `@pytest.mark.eval`
- Uses real LLM calls (not TestModel)
- 2-3 test cases for plan quality dimension

## Test Cases
Define cases that test different planning scenarios:
1. **Simple goal** - Should produce 1-3 focused tasks
2. **Complex goal** - Should decompose into logical sequence
3. **Ambiguous goal** - Should ask clarifying questions

## Pattern
```python
@pytest.mark.eval
@pytest.mark.asyncio
@pytest.mark.parametrize("case", PLAN_QUALITY_CASES, ids=[c["name"] for c in PLAN_QUALITY_CASES])
async def test_plan_quality(case: dict) -> None:
    plan = await plan_tasks(case["goal"])

    eval_prompt = f"Goal: {case['goal']}\nTasks: {plan.tasks}\nQuestions: {plan.questions}"
    score = await evaluate(EvalDimension.PLAN_QUALITY, eval_prompt)

    assert score.passed, f"Score {score.score}/5: {score.reasoning}"
```

## Validation
- [ ] `pytest -m eval nanoagent/tests/evals/plan_quality_eval.py -v` runs with real LLM
- [ ] At least 2/3 cases pass (score >= 3)
- [ ] Judge produces meaningful reasoning

## Files
- `nanoagent/tests/evals/__init__.py` (create)
- `nanoagent/tests/evals/cases.py` (create with PLAN_QUALITY_CASES)
- `nanoagent/tests/evals/plan_quality_eval.py` (create)
