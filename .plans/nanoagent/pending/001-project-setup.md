# Task 001: Project Setup and Quality Tools

**Iteration:** Foundation
**Status:** Pending
**Dependencies:** None
**Files:** pyproject.toml, .gitignore, .pre-commit-config.yaml, README.md

## Description
Initialize Python project with uv, configure quality tools (ruff 120-char lines, basedpyright strict, pytest async), set up pre-commit hooks with uv integration, and create flat project structure with tests next to source code.

## Working Result
- Project initialized with uv and Python 3.14
- Quality tools configured and working (ruff, basedpyright, pytest)
- Pre-commit hooks configured with sync-with-uv for version management
- uv.lock committed to git for reproducibility
- Project structure: nanoagent/core/, nanoagent/models/, nanoagent/tools/
- All quality checks passing (`uv run check`)
- Pre-commit hooks run successfully on empty project

## Validation
- [ ] `uv sync` successfully installs all dependencies
- [ ] `uv run format` runs without errors
- [ ] `uv run lint` runs without errors
- [ ] `uv run typecheck` runs without errors
- [ ] `uv run test` runs without errors (no tests yet, but pytest works)
- [ ] `pre-commit run --all-files` passes
- [ ] Project structure exists: nanoagent/{core,models,tools}/
- [ ] uv.lock exists and is tracked in git

## LLM Prompt
<prompt>
**Goal:** Establish a reproducible Python 3.14 project with integrated quality tools and pre-commit automation that eliminates version drift

**Constraints:**
- Must use uv as package manager (2025 standard)
- Python 3.14 required
- Line length: 120 characters
- Basedpyright in strict mode
- Pre-commit must sync versions from uv.lock (no version drift)
- uv.lock must be committed for reproducibility
- Flat project structure (nanoagent/ not src/nanoagent/)
- Tests next to source code (*_test.py pattern)

**Implementation Guidance:**
- Initialize as uv package project with appropriate name
- Set up Python 3.14 via uv python management
- Create directory structure for core, models, and tools modules
- Add production dependencies: pydantic, pydantic-ai, anthropic
- Add dev dependencies: pytest, pytest-asyncio, ruff, basedpyright, pre-commit
- Configure tool settings in pyproject.toml following plan.md § Research Findings > "Quality Tools Configuration"
- Set up pre-commit hooks following plan.md § Research Findings > "Pre-commit with uv Integration"
- Create .gitignore to exclude caches but KEEP uv.lock
- Create minimal README with project overview
- Install pre-commit git hooks
- Verify all quality checks pass on empty project

**Established Patterns:**
- See plan.md § Research Findings > "Quality Tools Configuration" for pyproject.toml tool settings
- See plan.md § Research Findings > "Pre-commit with uv Integration" for .pre-commit-config.yaml

**Validation:**
- Run `uv sync` - should complete without errors
- Run `uv run check` - all tools should run successfully
- Run `pre-commit run --all-files` - should pass
- Verify uv.lock exists and is tracked in git
- Confirm directory structure matches: nanoagent/{core,models,tools}/
</prompt>

## Notes

**planning:** Foundation task. All subsequent work depends on this. The pre-commit hooks use sync-with-uv to eliminate version drift between uv.lock and .pre-commit-config.yaml. Tests live next to source code (discovered via pytest's *_test.py pattern). uv.lock is committed for reproducibility. Pytest is NOT in pre-commit hooks (too slow) - run separately via `uv run test`.
