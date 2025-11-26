# Task 007: Create eval framework models (TDD)

## Goal
Create EvalDimension enum and EvalScore model with unit tests.

## Context
- Files: `nanoagent/evals/models.py`, `nanoagent/evals/models_test.py`
- Foundation for LLM-as-judge - must be solid before building judge
- Follow existing patterns in `nanoagent/models/schemas.py`

## Constraints
- EvalScore must be valid Pydantic AI output type
- Score range 1-5 with validation
- `passed` property must compare score to threshold
- ~30 LOC for models, ~20 LOC for tests

## TDD Approach

### Step 1: Write failing tests first
```python
# models_test.py
class TestEvalDimension:
    def test_has_four_dimensions(self) -> None:
        assert len(EvalDimension) == 4

class TestEvalScore:
    def test_passed_when_score_meets_threshold(self) -> None:
        score = EvalScore(dimension=EvalDimension.PLAN_QUALITY, score=3, reasoning="Acceptable")
        assert score.passed is True

    def test_failed_when_score_below_threshold(self) -> None:
        score = EvalScore(dimension=EvalDimension.PLAN_QUALITY, score=2, reasoning="Poor quality")
        assert score.passed is False

    def test_invalid_score_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            EvalScore(dimension=EvalDimension.PLAN_QUALITY, score=6, reasoning="Invalid")
```

### Step 2: Implement models to pass tests

### Step 3: Verify all quality checks pass

## Validation
- [ ] `pytest nanoagent/evals/models_test.py` passes
- [ ] `uv run basedpyright nanoagent/evals/` passes
- [ ] `uv run ruff check nanoagent/evals/` passes

## Files
- `nanoagent/evals/__init__.py` (create)
- `nanoagent/evals/models.py` (create)
- `nanoagent/evals/models_test.py` (create)
