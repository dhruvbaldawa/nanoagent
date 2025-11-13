# Plan: Nanoagent

## Overview

Lightweight multi-agent framework (<500 LOC) with Pydantic AI for autonomous task execution. Uses planning → execution → reflection cycles with pluggable tools and real-time streaming.

## Success Criteria (Milestone 1 Complete When...)

- [ ] Project initialized with uv, Python 3.14, quality tools (ruff, basedpyright, pytest), pre-commit hooks
- [ ] All 5 data models defined with comprehensive validation tests
- [ ] TodoManager implemented with priority-based task queue and unit tests
- [ ] TaskPlanner agent produces valid TaskPlanOutput with real LLM calls (validates Critical Risk #1)
- [ ] Executor agent executes tasks with tool calling support and tests (validates Critical Risk #1)
- [ ] Reflector agent identifies gaps and suggests new tasks with tests (validates Critical Risk #3)
- [ ] Manual orchestration POC completes one full cycle: plan → execute → reflect (validates Critical Risk #2)
- [ ] All tests passing with TDD approach followed throughout

---

## Milestones

### Milestone 1: Foundation 📋 Not Started (0%)
**Outcome**: Pydantic AI agents reliably coordinate through structured outputs, proving all Critical + Unknown risks are manageable

**Deliverables:**
- [ ] Project initialized with uv, Python 3.14, quality tools (ruff, basedpyright, pytest), pre-commit hooks
- [ ] All 5 data models defined with comprehensive validation tests (Task, TaskPlanOutput, ExecutionResult, ReflectionOutput, AgentRunResult)
- [ ] TodoManager implemented with priority-based task queue and unit tests
- [ ] TaskPlanner agent produces valid TaskPlanOutput with real LLM calls (validates Critical Risk #1)
- [ ] Executor agent executes tasks with tool calling support and tests (validates Critical Risk #1)
- [ ] Reflector agent identifies gaps and suggests new tasks with tests (validates Critical Risk #3)
- [ ] Manual orchestration POC completes one full cycle: plan → execute → reflect (validates Critical Risk #2)

**Risk Focus**: Critical + Unknown (Pydantic AI structured outputs, agent coordination, reflection quality, streaming patterns)

**Deferred to Next Planning Cycle:**
- Full orchestration loop automation
- Streaming implementation
- Tool registry extensibility
- Multiple built-in tool implementations

---

### Milestone 2: Integration
**Status**: 📅 To Be Planned (after Milestone 1 completion)

**Outcome**: Automated multi-iteration orchestration with pluggable tool system works end-to-end for diverse goal types

**Planned Deliverables** (will be refined based on M1 learnings):
- ToolRegistry for pluggable tools
- Built-in tools (web_search, read_file, write_file, execute_code)
- Automated Orchestrator loop
- StreamManager for event emission
- End-to-end tests for multiple goal types

**Note**: Tasks for Milestone 2 will be generated after Milestone 1 completion and review of learnings.

---

### Milestone 3: Production Hardening
**Status**: 📅 To Be Planned (after Milestone 2 completion)

**Outcome**: Production-ready framework with comprehensive testing, error handling, performance validation, and documentation

**Planned Deliverables** (will be refined based on M1 & M2 learnings):
- Edge case testing and error recovery
- Performance validation
- Token tracking and rate limiting
- Comprehensive documentation and examples

**Note**: Tasks for Milestone 3 will be generated after Milestone 2 completion.

---

**Overall Progress**: M0/M3 complete (0%) - Currently planning Milestone 1

---

## Risk Analysis

### Critical + Unknown (Foundation - Must Prove First)

1. **Pydantic AI Structured Output Reliability**
   - **Risk:** Entire system depends on reliably parsing TaskPlanOutput, ExecutionResult, ReflectionOutput
   - **Impact:** If structured outputs fail or hallucinate fields, coordination breaks down
   - **Mitigation:** Write tests first, validate with real prompts before orchestration

2. **Agent Coordination Context Passing**
   - **Risk:** Complex state flows between planner → executor → reflector
   - **Impact:** Agents may lose context, produce irrelevant tasks, or fail to converge
   - **Mitigation:** Test-driven approach for each handoff, validate context preservation

3. **Reflection Loop Quality**
   - **Risk:** Reflector might not identify real gaps, or loop forever adding tasks
   - **Impact:** System either terminates too early or runs indefinitely
   - **Mitigation:** Test reflection with multiple goal types, implement hard iteration limits

4. **Streaming Implementation**
   - **Risk:** Pydantic AI streaming patterns unclear from docs
   - **Impact:** Poor UX without real-time feedback
   - **Mitigation:** Build minimal streaming example first, can defer if blocking

### Critical + Known (Integration - Next Planning Cycle)

1. **Tool Registry Pattern** - Standard plugin architecture, well-understood
2. **Task Queue Management** - Simple priority queue with dict storage
3. **Orchestration Control Flow** - Well-defined in DESIGN.md

### Non-Critical (Hardening - Future Planning Cycle)

1. **Persistence** - Explicitly marked as extension point in DESIGN.md
2. **Human-in-the-Loop** - Extension point, not MVP
3. **MCP Integration** - Extension point, not MVP
4. **Multiple Executor Specialization** - Premature, test generic first

---

## Architecture

**Update as implementation progresses**

**Planned Project Structure (Milestone 1):**
```
nanoagent/
├── core/
│   ├── task_planner.py + task_planner_test.py (~50 LOC)
│   ├── executor.py + executor_test.py (~80 LOC)
│   ├── reflector.py + reflector_test.py (~60 LOC)
│   ├── todo_manager.py + todo_manager_test.py (~60 LOC)
│   └── integration_test.py (manual orchestration POC)
└── models/
    ├── schemas.py + schemas_test.py (~40 LOC)

M1 Core: ~290 LOC (excluding tests)
```

**To be added in future milestones:**
- orchestrator.py (~150 LOC) - Milestone 2
- stream_manager.py (~30 LOC) - Milestone 2
- tools/registry.py (~30 LOC) - Milestone 2
- tools/builtin.py (~100 LOC) - Milestone 2

**Key Patterns:**
- **TDD Throughout:** Every component follows: Write failing test → Implement → Tests pass → Refactor
- **Tests Next to Source:** `*_test.py` files alongside implementation files
- **Async-First:** All agents and tools use async/await patterns
- **Flat Package Structure:** `nanoagent/` instead of `src/nanoagent/` for simplicity
- **Quality Enforcement:** Pre-commit hooks run ruff, basedpyright, pytest on every commit

**Agent Coordination (Milestone 1 POC):**
1. TaskPlanner decomposes goal → TaskPlanOutput (list of tasks)
2. TodoManager queues tasks by priority
3. Executor executes next task → ExecutionResult
4. Reflector evaluates progress → ReflectionOutput (done flag, gaps, new_tasks)
5. Manual coordination in integration test (automated in Milestone 2)

---

## Task History

**Completed** (in completed/):
- None yet

**In Flight**:
- None yet

**Pending** (Milestone 1 - need to be created):
- `001-project-setup.md` - Initialize project with uv, Python 3.14, quality tools, pre-commit hooks
- `002-data-models.md` - Define 5 Pydantic models with validation tests (TDD)
- `003-todo-manager.md` - Implement task queue with priority management (TDD)
- `004-task-planner.md` - TaskPlanner agent with structured output validation (TDD, Critical Risk #1)
- `005-executor-agent.md` - Executor agent with tool calling support (TDD, Critical Risk #1)
- `006-reflector-agent.md` - Reflector agent with gap detection (TDD, Critical Risk #3)
- `007-manual-orchestration-poc.md` - Manual POC proves full cycle works (Milestone 1 validation)

**Status tracked via file location:** `pending/` → `implementation/` → `review/` → `testing/` → `completed/`

---

## Next Planning Cycle

### After Milestone 1 Completion

**Trigger**: Task 007 (manual orchestration POC) passes integration test

**Review Questions**:
1. Did Pydantic AI structured outputs work reliably? Any parsing issues?
2. Was context passing between agents seamless?
3. Did reflection produce sensible gap identification?
4. What was the actual LOC count for M1 components?
5. What prompt patterns worked best for each agent?
6. Any architectural adjustments needed before M2?

**Actions**:
1. Review all M1 learnings and update Architecture section
2. Update risk analysis - move proven risks to "Critical + Known"
3. Generate Milestone 2 task files (008-0XX) based on actual M1 architecture
4. Refine M2 deliverables based on learnings
5. Update deferred items list for relevance

**Expected Learnings**:
- Pydantic AI agent patterns and best practices
- Optimal prompt structures for each agent type
- Context dict structure that works best for handoffs
- Reflection frequency sweet spot (every N iterations)
- Tool calling patterns needed for M2 executor
- Whether streaming is critical or can be deferred

### After Milestone 2 Completion

**Trigger**: Milestone 2 end-to-end tests pass for 3+ goal types

**Actions**:
1. Review M2 performance characteristics
2. Identify common error modes for M3 hardening
3. Generate Milestone 3 task files
4. Adjust M3 scope based on actual LOC budget remaining

---

## Deferred Items

### To Milestone 2 (Next Planning Cycle)
- Full orchestration loop automation - tasks to be created after M1
- Streaming implementation - defer if not critical, validate in M1 POC
- Tool registry extensibility - tasks to be created after M1
- Multiple built-in tool implementations - tasks to be created after M1

### To Milestone 3 (Future Planning Cycle)
- Advanced streaming (SSE/WebSocket) - if simple events insufficient
- Tool approval/human-in-loop - if needed for production use
- Complex error recovery strategies - based on M2 error patterns

### To Post-MVP
- **Persistence** - In-memory sufficient for MVP; DESIGN.md shows trivial addition later
- **Human-in-the-Loop approval flows** - Not required for autonomous operation validation
- **MCP Integration** - Extension point, not core functionality
- **Multi-agent specialization** - Need to prove generic executor first
- **Cost optimization** - Use consistent model, optimize after proving functionality
- **Real-time UI/frontend** - Framework is backend-focused

### Eliminated
- None yet - will update as M1 implementation reveals unnecessary items

---

## Research Findings

### Pre-commit with uv Integration
**Decision**: Use sync-with-uv to eliminate version drift between uv.lock and .pre-commit-config.yaml
**Research**: Investigated 2025 best practices for pre-commit + uv integration. Found that tools specified in both pyproject.toml and .pre-commit-config.yaml create version drift issues.
**Validated Approach**:
```yaml
repos:
  # FIRST: Sync tool versions from uv.lock to pre-commit
  - repo: https://github.com/tsvikas/sync-with-uv
    rev: v0.1.0
    hooks:
      - id: sync-with-uv

  # Keep uv.lock in sync with pyproject.toml
  - repo: https://github.com/astral-sh/uv-pre-commit
    rev: 0.9.9
    hooks:
      - id: uv-lock

  # Standard hygiene hooks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-added-large-files

  # Ruff (version auto-synced from uv.lock by sync-with-uv)
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.14.4
    hooks:
      - id: ruff-check
        args: [--fix]
      - id: ruff-format

  # Basedpyright (version auto-synced from uv.lock)
  - repo: https://github.com/DetachHead/basedpyright-pre-commit-mirror
    rev: v1.13.0
    hooks:
      - id: basedpyright
```
References:
- https://pydevtools.com/blog/sync-with-uv-eliminate-pre-commit-version-drift/
- https://docs.astral.sh/uv/guides/integration/pre-commit/
- https://docs.basedpyright.com/latest/installation/pre-commit%20hook/

### Quality Tools Configuration
**Decision**: Use ruff for linting/formatting, basedpyright for type checking, pytest for testing (2025 standard)
**Research**: Evaluated modern Python quality toolchain. Ruff replaces flake8/black/isort. Basedpyright provides strict type checking. Line length 120 balances readability and modern displays.
**Validated Approach**:
```toml
[tool.ruff]
line-length = 120
lint.select = ["E", "F", "I", "B", "UP", "S", "RET", "N"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

[tool.basedpyright]
typeCheckingMode = "strict"
pythonVersion = "3.14"

[tool.pytest.ini_options]
testpaths = ["nanoagent"]
python_files = ["*_test.py"]
asyncio_mode = "auto"
addopts = "-ra --strict-markers"

[tool.uv.scripts]
format = "ruff format ."
lint = "ruff check ."
typecheck = "basedpyright"
test = "pytest"
check = "ruff check . && basedpyright && pytest"
```
References:
- https://docs.astral.sh/ruff/
- https://docs.basedpyright.com/
- https://docs.pytest.org/

### Python .gitignore Patterns
**Decision**: Exclude caches and temporary files, but KEEP uv.lock for reproducibility
**Validated Approach**:
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# Virtual environments (uv manages this)
.venv/
env/
venv/

# Testing
.pytest_cache/
.coverage
htmlcov/

# Linting/Type checking
.ruff_cache/
.mypy_cache/
.pyright/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Keep uv.lock for reproducibility - DO NOT ADD TO GITIGNORE
```

---

## Project-Level Success Criteria (All Milestones)

**Technical:**
- Core framework stays <500 LOC (excluding tests)
- All quality checks pass (ruff, basedpyright strict, pytest)
- Test coverage >80% throughout development
- Pre-commit hooks enforce quality on every commit

**Functional:**
- Successfully completes 3+ different goal types autonomously (research, calculation, file ops)
- Structured outputs parse reliably (>95% success rate in tests)
- Converges to goal completion within reasonable iterations
- All tests pass at every milestone

**Note**: These are evaluated at project completion (end of M3), not at M1 completion.
