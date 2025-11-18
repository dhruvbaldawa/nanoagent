# Plan: Nanoagent

## Overview

Lightweight multi-agent framework (<500 LOC) with Pydantic AI for autonomous task execution. Uses planning → execution → reflection cycles with pluggable tools and real-time streaming.

## Success Criteria (Milestone 1 Complete When...)

- [x] Project initialized with uv, Python 3.14, quality tools (ruff, basedpyright, pytest), pre-commit hooks
- [x] All 5 data models defined with comprehensive validation tests
- [x] TodoManager implemented with priority-based task queue and unit tests
- [x] TaskPlanner agent produces valid TaskPlanOutput with real LLM calls (validates Critical Risk #1)
- [x] Executor agent executes tasks with tool calling support and tests (validates Critical Risk #1)
- [x] Reflector agent identifies gaps and suggests new tasks with tests (validates Critical Risk #3)
- [x] Manual orchestration POC completes one full cycle: plan → execute → reflect (validates Critical Risk #2)
- [x] All tests passing with TDD approach followed throughout

**✅ MILESTONE 1 COMPLETE** - All foundation components implemented and validated

---

## Milestones

### Milestone 1: Foundation ✅ Complete (100%)
**Outcome**: Pydantic AI agents reliably coordinate through structured outputs, proving all Critical + Unknown risks are manageable

**Deliverables:**
- [x] Project initialized with uv, Python 3.14, quality tools (ruff, basedpyright, pytest), pre-commit hooks
- [x] All 5 data models defined with comprehensive validation tests (Task, TaskPlanOutput, ExecutionResult, ReflectionOutput, AgentRunResult)
- [x] TodoManager implemented with priority-based task queue and unit tests
- [x] TaskPlanner agent produces valid TaskPlanOutput with real LLM calls (validates Critical Risk #1)
- [x] Executor agent executes tasks with tool calling support and tests (validates Critical Risk #1)
- [x] Reflector agent identifies gaps and suggests new tasks with tests (validates Critical Risk #3)
- [x] Manual orchestration POC completes one full cycle: plan → execute → reflect (validates Critical Risk #2)

**Risk Validation**: ✅ ALL CRITICAL RISKS PROVEN MANAGEABLE
- Risk #1 (Structured Outputs): ✅ Pydantic AI reliably produces correct structured outputs
- Risk #2 (Agent Coordination): ✅ Context flows correctly through plan → execute → reflect
- Risk #3 (Reflection Quality): ✅ Reflector identifies gaps and suggests actionable tasks

**Architecture Learnings:**
- **LOC Actual**: 618 LOC for M1 core (schemas 78, todo_manager 89, task_planner 125, executor 141, reflector 185)
- **Multi-Provider Support**: Added config.py (102 LOC) for per-agent model selection (anthropic/openai/openrouter)
- **TDD Success**: All components built test-first, 117 tests passing
- **Error Handling**: Comprehensive input validation and error recovery in all agents
- **Streaming**: Deferred to M2 (not blocking, manual POC works without it)

---

### Milestone 2: Integration
**Status**: 📋 Planning Complete - Ready for Implementation (0%)

**Outcome**: Automated multi-iteration orchestration with pluggable tool system works end-to-end for diverse goal types

**Deliverables** (refined based on M1 learnings):
- [ ] ToolRegistry for pluggable tools (simple dict-based, ~30 LOC)
- [ ] Built-in tools (minimal mock tools for testing - calculator, echo, timestamp)
- [ ] Automated Orchestrator loop (~150 LOC, proven pattern from M1 Task 007)
- [ ] StreamManager for event emission (simple JSON print, ~30 LOC)
- [ ] End-to-end tests for 3+ diverse goal types (calculation, multi-step, iterative)

**M1 Learnings Applied:**
- Use proven context dict pattern from M1
- Follow M1 agent call patterns (plan_tasks, execute_task, reflect_on_progress)
- Reflection every 3 iterations (validated in M1)
- TDD approach throughout (M1 success pattern)
- Real LLM calls in tests (no mocking agents)

**Deferred to M3:**
- Real tools (web_search, file ops, code execution) - keeping M2 simple with mock tools
- Advanced streaming (SSE/WebSocket) - simple JSON print sufficient for M2
- Tool approval/human-in-loop - not needed for autonomous validation

**Estimated LOC:** ~210 LOC for M2 components (registry 30, builtin 60, orchestrator 150, stream_manager 30) - staying well under 500 LOC budget

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

**Overall Progress**: M1/M3 complete (33%) - Milestone 1 validated, planning Milestone 2

---

## Risk Analysis

### ✅ Critical Risks - PROVEN (M1 Validation Complete)

1. **Pydantic AI Structured Output Reliability** - ✅ VALIDATED
   - **Original Risk:** Entire system depends on reliably parsing TaskPlanOutput, ExecutionResult, ReflectionOutput
   - **M1 Validation:** All agents reliably produce correct structured outputs across 117 tests
   - **Key Learning:** Pydantic AI result_type parameter with well-defined models works flawlessly

2. **Agent Coordination Context Passing** - ✅ VALIDATED
   - **Original Risk:** Complex state flows between planner → executor → reflector
   - **M1 Validation:** Context dict pattern works seamlessly, integration test proves end-to-end coordination
   - **Key Learning:** Simple dict[task_id, result] structure sufficient for context passing

3. **Reflection Loop Quality** - ✅ VALIDATED
   - **Original Risk:** Reflector might not identify real gaps, or loop forever adding tasks
   - **M1 Validation:** Reflector produces sensible gap identification and new task suggestions
   - **Key Learning:** Comprehensive prompts with done_tasks and pending_tasks context produce high-quality reflection

### Critical + Known (M2 Integration - Ready to Implement)

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
- ✅ `001-project-setup.md` - M1: Project initialized with uv, Python 3.14, quality tools, pre-commit hooks
- ✅ `002-data-models.md` - M1: All 5 Pydantic models with comprehensive validation tests (45 tests)
- ✅ `003-todo-manager.md` - M1: TodoManager with priority-based task queue (8 tests)
- ✅ `004-task-planner.md` - M1: TaskPlanner agent with structured output validation (14 tests) - ✅ Risk #1 proven
- ✅ `005-executor-agent.md` - M1: Executor agent with tool calling support (22 tests) - ✅ Risk #1 proven
- ✅ `006-reflector-agent.md` - M1: Reflector agent with gap detection (26 tests) - ✅ Risk #3 proven
- ✅ `007-manual-orchestration-poc.md` - M1: Integration test validates complete cycle - ✅ Risk #2 proven, **MILESTONE 1 COMPLETE**

**In Flight**:
- None (planning M2 tasks)

**Pending** (Milestone 2 - ready for implementation):
- `008-tool-registry.md` - ToolRegistry for pluggable tools (~30 LOC)
- `009-built-in-tools.md` - Minimal built-in tools for testing (~60 LOC)
- `010-orchestrator.md` - Automated orchestration loop (~150 LOC)
- `011-stream-manager.md` - Event streaming for visibility (~30 LOC)
- `012-end-to-end-tests.md` - E2E validation for 3+ goal types (M2 VALIDATION)

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
