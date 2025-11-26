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
- [ ] `pytest --collect-only` shows eval tests deselected
- [ ] `pytest --collect-only -m eval` shows only eval tests
- [ ] Pre-commit hooks pass

## Files
- `pyproject.toml` (modify)
