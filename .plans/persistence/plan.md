# Plan: Persistence

## Overview

Add persistence to nanoagent so orchestration state can be saved/restored. Enables resuming long-running orchestrations and running multiple concurrent orchestrations with isolated state.

## Design Decisions (from brainstorming)

| Decision | Choice |
|----------|--------|
| Source of truth | State store (not in-memory) |
| Read pattern | Always from store |
| Write pattern | Always to store |
| Concurrency | Multiple runs via run_id scoping |
| Resume granularity | Last checkpoint before LLM call |
| Store interface | Domain-aware, composable (3 protocols) |
| First backend | SQLite |
| In-memory structures | Eliminated for simplicity |

## Store Interface Design

Three composable protocols (single responsibility):

```python
class RunStore(Protocol):
    def create(self, run_id: str, goal: str, max_iterations: int) -> None
    def get(self, run_id: str) -> RunState | None
    def list(self) -> list[str]
    def update_loop_state(self, run_id: str, phase: str, iteration: int, current_task_id: str | None) -> None

class TaskStore(Protocol):
    def save(self, run_id: str, task: Task) -> None
    def get_all(self, run_id: str) -> list[Task]
    def get_pending(self, run_id: str) -> list[Task]

class ContextStore(Protocol):
    def save_result(self, run_id: str, task_id: str, result: str) -> None
    def get_all(self, run_id: str) -> dict[str, str]
```

SQLite backend implements all three:

```python
class SQLiteStore(RunStore, TaskStore, ContextStore):
    ...
```

## Impact on Existing Code

- `TodoManager` - becomes thin facade over `TaskStore`
- `Orchestrator` - uses `RunStore` + `ContextStore` instead of instance variables
- `StreamManager`, `ToolRegistry`, agents - unchanged (stateless/transient)

## Risk Analysis

| Risk | Type | Classification | Status |
|------|------|----------------|--------|
| Resume at exact loop position | Architecture | Critical + Unknown | **RESOLVED** (M1 POC) |
| SQLite concurrent access | Integration | Critical + Unknown | **RESOLVED** (WAL mode works) |
| Refactoring breaks existing tests | Architecture | Critical + Known | Active (M2/M3) |
| Schema design | Architecture | Critical + Known | **RESOLVED** |
| Performance (read every access) | Performance | Non-Critical | Deferred |
| Schema migrations | Operations | Non-Critical | Deferred |

### M1 Learnings

1. **Resume semantics**: Checkpoint before LLM execution. If crash between "task done" and "checkpoint", task re-executes on resume (acceptable idempotency).
2. **Minimal state**: `run_id`, `phase`, `iteration`, `current_task_id` sufficient for resume.
3. **Protocol design**: Composable protocols work well - components depend only on what they need.

## Milestones

### Milestone 1: Prototype + Store Foundation ✓ COMPLETE

**Goal:** Validate the two Critical+Unknown risks before building full infrastructure.

**Outcome:** Both risks resolved. POC validates resume semantics, SQLite and MemoryStore implementations complete with 53 tests.

**Deliverables:**
- `scripts/resume_poc.py` - throwaway POC (validated approach)
- `nanoagent/persistence/protocols.py` - Protocol definitions + RunState/Phase models
- `nanoagent/persistence/sqlite_store.py` - SQLite implementation (WAL mode)
- `nanoagent/persistence/memory_store.py` - In-memory implementation
- 53 persistence tests covering all protocols

### Milestone 2: Refactor TodoManager ← CURRENT

**Goal:** Replace in-memory storage with `TaskStore` dependency.

**Tasks:**
- `pending/002-todomanager-refactor.md` - Inject TaskStore dependency, keep backward compatibility

**Success criteria:**

- *Minimum:* All existing TodoManager tests pass unchanged
- *Complete:* Tasks persist across TodoManager instantiations (same run_id)

### Milestone 3: Refactor Orchestrator

**Goal:** Replace in-memory context/iteration with `RunStore` + `ContextStore`, enable resume.

**Tasks:**
- `pending/003-orchestrator-persistence.md` - Inject stores, checkpoint loop state
- `pending/004-orchestrator-resume.md` - Implement `Orchestrator.resume(run_id)` method

**Success criteria:**

- *Minimum:* Orchestrator uses stores, all existing tests pass
- *Complete:* Can stop and resume at any checkpoint, re-runs task if crashed mid-LLM-call

### Milestone 4: End-to-End Validation

**Goal:** Prove the full flow works with real orchestration scenarios.

**Tasks:**

1. E2E test: start orchestration, kill, resume, complete
2. E2E test: multiple concurrent orchestrations
3. Update evals if needed

**Success criteria:**

- *Minimum:* Resume produces same final result as uninterrupted run
- *Complete:* Concurrent runs don't interfere, evals pass

---

## Implementation Strategy

**Approach:**

- **Prototype First**: M1 starts with throwaway POC to validate resume semantics before formalizing protocols
- **Core Before Polish**: Build store layer (M1) before refactoring existing components (M2-M3)
- **Integration Early**: SQLite concurrent access validated in M1, not deferred

**Quality Gates:**

- All code must have tests (TDD per project guidelines)
- basedpyright strict mode passes
- ruff passes
- Existing tests must stay green during refactoring (M2, M3)

**Technology:**

- SQLite with WAL mode (stdlib, no new dependencies)
- Pydantic models for store data types (consistent with existing codebase)
- `typing.Protocol` for store interfaces (structural subtyping)

---

## Execution Framework

**Definition of Done (per task):**

- Code implemented
- Tests pass (TDD)
- basedpyright passes
- ruff passes
- Task moved to `completed/`

**Sprint Cadence:**

- Plan 1-2 tasks at a time (don't over-plan)
- Review deferred items after each milestone

**Deferral Review Schedule:**

- After M1: Re-evaluate JSON backend need
- After M3: Re-evaluate caching need based on observed performance
- After M4: Re-evaluate schema migration need

---

## Deferred

- JSON file backend (add if someone needs zero dependencies)
- Schema migrations/versioning (add when schema changes)
- Caching layer (add if performance becomes an issue)
- Run cleanup/garbage collection (add when needed)

## Task History

### Completed

- **001-store-protocols-sqlite** (M1): Resume POC + Store Foundation
  - POC validated resume semantics (checkpoint before execution)
  - Three protocols: `RunStore`, `TaskStore`, `ContextStore`
  - Two implementations: `SQLiteStore` (WAL mode), `MemoryStore`
  - Security: path traversal protection, FK constraints, error handling
  - 53 persistence tests, full suite 282/282 passing
