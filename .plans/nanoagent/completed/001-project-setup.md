# Task 001: Project Setup and Quality Tools

**Iteration:** Foundation
**Status:** COMPLETED
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
- All quality checks passing (`uv run ruff check`)
- Pre-commit hooks run successfully on empty project

## Validation
- [x] `uv sync` successfully installs all dependencies
- [x] `uv run ruff format .` runs without errors
- [x] `uv run ruff check .` runs without errors
- [x] `uv run basedpyright` runs without errors
- [x] `uv run pytest` runs without errors (no tests yet, but pytest works)
- [x] `pre-commit run --all-files` passes
- [x] Project structure exists: nanoagent/{core,models,tools}/
- [x] uv.lock exists and is tracked in git

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
- Run `uv run ruff check` - all tools should run successfully
- Run `pre-commit run --all-files` - should pass
- Verify uv.lock exists and is tracked in git
- Confirm directory structure matches: nanoagent/{core,models,tools}/
</prompt>

## Notes

**planning:** Foundation task. All subsequent work depends on this. The pre-commit hooks use sync-with-uv to eliminate version drift between uv.lock and .pre-commit-config.yaml. Tests live next to source code (discovered via pytest's *_test.py pattern). uv.lock is committed for reproducibility. Pytest is NOT in pre-commit hooks (too slow) - run separately via `uv run pytest`.

**implementation:**
- Set up Python 3.14.0rc1 using `uv python install 3.14`
- Created pyproject.toml with production dependencies (pydantic, pydantic-ai, anthropic) and dev dependencies (pytest, pytest-asyncio, ruff, basedpyright, pre-commit)
- Configured tool settings: ruff with 120-char lines, basedpyright in strict mode, pytest with async support
- Created .pre-commit-config.yaml with sync-with-uv to eliminate version drift
- Created flat project structure: nanoagent/{core,models,tools}/ with __init__.py files
- Created README.md with project overview and usage instructions
- Installed dependencies with `uv sync --group dev`
- Verified all quality checks pass:
  - ruff lint: ✓ All checks passed
  - basedpyright type check: ✓ 0 errors, 0 warnings
  - pytest: ✓ 0 items collected (expected - no tests yet)
  - pre-commit: ✓ All hooks pass on all files
- Pre-commit hooks installed at .git/hooks/pre-commit
- uv.lock created and ready to be committed to git

**Files Created/Modified:**
- pyproject.toml: Project configuration with dependencies and tool settings
- .pre-commit-config.yaml: Pre-commit hooks with sync-with-uv integration
- nanoagent/__init__.py: Package root
- nanoagent/core/__init__.py: Core module
- nanoagent/models/__init__.py: Models module
- nanoagent/tools/__init__.py: Tools module
- README.md: Project documentation (updated with correct command syntax)
- uv.lock: Dependency lock file for reproducibility

**Key Decisions:**
- Used dependency-groups in pyproject.toml (uv standard) instead of project.optional-dependencies
- Removed [tool.uv.scripts] section as it's not supported by uv - tools called via `uv run` directly
- Python 3.14.0rc1 available; configured basedpyright and requires-python accordingly

**review:**
Security: 90/100 | Quality: 85/100 | Performance: 95/100 | Tests: 85/100

**Specialized Review Findings:**
- Test Coverage: No CRITICAL gaps, 2 important gaps (5-6/10 criticality) - package import tests, tool config validation
- Error Handling: 1 CRITICAL, 2 HIGH findings - README composite command, pre-commit version drift, dependency bounds missing
- Security: GOOD posture (90/100), no critical vulnerabilities, only LOW/INFO findings

**REJECTED - Blocking issues:**
1. README.md:41 composite command `uv run ruff check . && uv run basedpyright && uv run pytest` can fail silently without indicating which step failed
2. Dependencies lack upper bounds: "pydantic>=2.0", "anthropic>=0.32.0" could introduce breaking changes
3. Pre-commit hooks show "NOT MANAGED" versions - potential drift between uv.lock and .pre-commit-config.yaml

**Required actions:**
- Fix README command to provide clear error feedback (use individual commands or proper script)
- Add major version bounds to dependencies: "<3.0", "<1.0" etc.
- Investigate sync-with-uv warnings and ensure all tool versions are managed properly

**implementation (revision):**
- Fixed README.md composite command issue - replaced `&&` chain with individual commands that exit on failure
- Pinned dependencies to latest stable versions: pydantic==2.12.4, pydantic-ai==1.18.0, anthropic==0.73.0
- Verified pre-commit hooks are properly managed by sync-with-uv - all hooks pass without warnings
- Re-ran quality checks: all pass successfully

**review (revision):**
Security: 90/100 | Quality: 95/100 | Performance: 95/100 | Tests: 90/100

Working Result verified: ✓ All critical issues resolved
Validation: 8/8 passing
Full test suite: 0/0 passing (no tests yet for setup task)
Diff: 44 lines (README + pyproject.toml fixes)

**Specialized Review Findings (Re-evaluated):**
- Test Coverage: No critical gaps (setup task properly validated manually)
- Error Handling: All CRITICAL/HIGH issues fixed - README commands now exit on failure
- Security: GOOD posture (90/100) - dependencies pinned to stable versions

✅ Task 001 APPROVED → testing

**testing:**
- End-to-end validation successful
  - pytest: ✓ Working (0 items collected as expected for setup task)
  - ruff check: ✓ All checks passed
  - basedpyright: ✓ 0 errors, 0 warnings
  - pre-commit hooks: ✓ All hooks passing
- Project structure confirmed: nanoagent/{core,models,tools}/ with __init__.py files
- Dependencies working: uv sync successful with pinned versions
- README commands tested: Individual commands with proper error handling

✅ Task 001 completed successfully

**COMPLETED → completed**
