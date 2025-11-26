# Task 008: Create LLM-as-judge evaluator (TDD)

## Goal
Create evaluator agent that scores agent outputs on quality dimensions.

## Context
- Files: `nanoagent/evals/judge.py`, `nanoagent/evals/judge_test.py`
- **Critical risk**: This is the core of Tier 2 - must validate judge works before building eval tests
- Uses Pydantic AI Agent pattern with EvalScore output type
- Unit tests use TestModel (no real LLM calls)

## Constraints
- Single evaluator agent with dimension-specific prompts
- `evaluate()` function takes dimension + prompt, returns EvalScore
- Reuse reflector model config
- ~40 LOC for judge, ~25 LOC for tests

## Risk Mitigation
This task validates the **Critical + Unknown** risk: Can we build an LLM-as-judge that produces structured EvalScore outputs reliably?

## TDD Approach

### Step 1: Write failing tests first
```python
# judge_test.py
from pydantic_ai.models.test import TestModel

class TestEvaluate:
    @pytest.mark.asyncio
    async def test_returns_eval_score(self) -> None:
        with evaluator.override(model=TestModel()):
            score = await evaluate(EvalDimension.PLAN_QUALITY, "Test prompt")
            assert isinstance(score, EvalScore)

    @pytest.mark.asyncio
    async def test_sets_dimension_correctly(self) -> None:
        with evaluator.override(model=TestModel()):
            score = await evaluate(EvalDimension.REFLECTION_ACCURACY, "Test prompt")
            assert score.dimension == EvalDimension.REFLECTION_ACCURACY

    @pytest.mark.asyncio
    async def test_respects_custom_threshold(self) -> None:
        with evaluator.override(model=TestModel()):
            score = await evaluate(EvalDimension.PLAN_QUALITY, "Test", pass_threshold=4)
            assert score.pass_threshold == 4
```

### Step 2: Implement judge to pass tests

### Step 3: Verify quality checks pass

## Guidance
- BASE_SYSTEM_PROMPT should define 1-5 scoring rubric clearly
- DIMENSION_PROMPTS dict maps each EvalDimension to evaluation criteria
- Review existing agent patterns in `nanoagent/core/`

## Validation
- [ ] `pytest nanoagent/evals/judge_test.py` passes
- [ ] `uv run basedpyright nanoagent/evals/` passes
- [ ] `uv run ruff check nanoagent/evals/` passes

## Files
- `nanoagent/evals/judge.py` (create)
- `nanoagent/evals/judge_test.py` (create)
- `nanoagent/evals/__init__.py` (update exports)
