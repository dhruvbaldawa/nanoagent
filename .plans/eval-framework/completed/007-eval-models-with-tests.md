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
- [x] `pytest nanoagent/evals/models_test.py` passes (9/9 tests)
- [x] `uv run basedpyright nanoagent/evals/` passes
- [x] `uv run ruff check nanoagent/evals/` passes

## Files
- `nanoagent/evals/__init__.py` (create) ✓
- `nanoagent/evals/models.py` (create) ✓
- `nanoagent/evals/models_test.py` (create) ✓

**Status:** READY_FOR_REVIEW

**implementation:**
- Step 1: Wrote 9 comprehensive unit tests covering EvalDimension enum and EvalScore model
- Step 2: Implemented EvalDimension enum with 4 quality dimensions and EvalScore Pydantic model
- Step 3: All tests passing (9/9), type checking clean, no linting issues
- Working Result verified: ✓ EvalScore validates score range 1-5, passed property works correctly, all dimensions defined
- Full test suite: 211/211 passing (including 9 new eval model tests)
- Files created:
  - `nanoagent/evals/__init__.py` - Exports EvalDimension and EvalScore
  - `nanoagent/evals/models.py` - Core models (~35 LOC)
  - `nanoagent/evals/models_test.py` - Comprehensive unit tests (~60 LOC)

**testing:**
Validated 9 tests (behavior-focused):
- EvalDimension enum: all 4 dimensions defined
- EvalScore validation: score range 1-5, passed property logic, custom thresholds
- Error handling: ValidationError on invalid scores, short reasoning

Test coverage: Statements 100% | Branches 100% | Functions 100%
Test breakdown: Unit: 9 | Integration: 0 | Total: 9
Full suite: 211/211 passing
Working Result verified: ✓ Models ready for use in judge evaluator

**review:**
Security: 85/100 | Quality: 95/100 | Performance: 100/100 | Tests: 95/100

Working Result verified: ✓ EvalDimension enum + EvalScore model fully functional and tested
Validation: 3/3 checkboxes passing
Full test suite: 211/211 passing
Diff: 143 total LOC (43 models + 94 tests + 6 init)

**Specialized Review Findings:**
- Test Coverage: No CRITICAL gaps (3 minor gaps 2-3/10 rated - all testing Pydantic framework behavior, not custom logic)
- Error Handling: Acceptable (2 MEDIUM findings: 1 already handled by Pydantic constraints, 1 recommendation for max_length on reasoning field for cost control - low priority)
- Security: No vulnerabilities detected (1 LOW confidence 40/100 finding - unbounded string input on reasoning field, mitigated by internal context, recommendation to add max_length=500 for future-proofing)

APPROVED → completed
