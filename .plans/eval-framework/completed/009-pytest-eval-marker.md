# Task 009: Configure pytest eval marker

## Goal
Configure pytest to skip eval tests by default and register the `eval` marker.

## Context
- File: `pyproject.toml`
- Eval tests use real LLM calls (slow, costs money)
- Must be configured before creating eval tests

## Constraints
- `pytest` should skip eval tests by default
- `pytest -m eval` should run only eval tests
- `pytest -m ""` should run everything

## Implementation
Add to `[tool.pytest.ini_options]`:
```toml
python_files = ["*_test.py", "*_eval.py"]
addopts = "-ra --strict-markers -m 'not eval'"
markers = [
    "eval: quality evaluations using real LLM calls (slow, costs money)",
]
```

## Validation
- [x] `pytest --collect-only` shows 229 tests collected (eval marker registered)
- [x] `pytest --markers` shows eval marker registered: "quality evaluations using real LLM calls (slow, costs money)"
- [x] Pre-commit hooks pass (ruff check passed)
- [x] Full test suite passes (229/229)

## Files
- `pyproject.toml` (modified)

## Status
APPROVED

**Implementation Complete:**
- ✓ Added python_files configuration for "*_test.py" and "*_eval.py"
- ✓ Updated addopts to include "-m 'not eval'" (skips eval tests by default)
- ✓ Added markers section with eval marker definition
- ✓ All pytest validations pass
- ✓ eval marker properly registered and documented

**Test Results:**
- ✓ 229 tests collected
- ✓ Full test suite passes
- ✓ Marker system working correctly
