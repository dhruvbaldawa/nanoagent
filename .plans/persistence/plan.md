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

| Risk | Type | Classification | Mitigation |
|------|------|----------------|------------|
| Resume at exact loop position | Architecture | **Critical + Unknown** | Prototype in M1 |
| SQLite concurrent access | Integration | **Critical + Unknown** | WAL mode, test in M1 |
| Refactoring breaks existing tests | Architecture | Critical + Known | Incremental refactor, keep tests green |
| Schema design | Architecture | Critical + Known | Standard DB patterns |
| Performance (read every access) | Performance | Non-Critical | Defer; add caching if proven slow |
| Schema migrations | Operations | Non-Critical | Defer; add versioning when schema changes |

## Milestones

### Milestone 1: Prototype + Store Foundation

**Goal:** Validate the two Critical+Unknown risks before building full infrastructure.

**Risk focus:**

- Can we checkpoint and resume at exact loop position?
- Does SQLite handle concurrent run_ids correctly?

**Tasks:**

1. Resume POC - minimal script that simulates orchestrator loop, checkpoints state, "crashes", resumes at correct position
2. Define store protocols (`RunStore`, `TaskStore`, `ContextStore`)
3. Implement `SQLiteStore` backing all three
4. Concurrent access tests

**Success criteria:**

- *Minimum:* POC demonstrates loop state save/restore works; SQLite round-trips data correctly
- *Complete:* Full protocol implementation with concurrent run isolation proven

**Exploration budget:** 30% - this is de-risking, expect some throwaway code

### Milestone 2: Refactor TodoManager

**Goal:** Replace in-memory storage with `TaskStore` dependency.

**Tasks:**

1. Refactor `TodoManager` to use `TaskStore`
2. Update existing tests
3. Ensure backward compatibility for tests that don't need persistence

**Success criteria:**

- *Minimum:* All existing TodoManager tests pass
- *Complete:* Tasks persist across TodoManager instantiations (same run_id)

### Milestone 3: Refactor Orchestrator

**Goal:** Replace in-memory context/iteration with `RunStore` + `ContextStore`, enable resume.

**Tasks:**

1. Refactor `Orchestrator` to use stores
2. Integrate loop state checkpointing from M1 POC
3. Implement `Orchestrator.resume(run_id)`
4. Update existing tests

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

(none yet)
