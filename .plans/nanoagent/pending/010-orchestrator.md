# Task 010: Automated Orchestrator Loop

**Iteration:** Integration
**Status:** Pending
**Dependencies:** 003, 004, 005, 006, 008 (TodoManager, all agents, ToolRegistry)
**Files:** nanoagent/core/orchestrator.py, nanoagent/core/orchestrator_test.py

## Description
Implement Orchestrator class that automates the planning → execution → reflection cycle. Coordinates all M1 components (TaskPlanner, Executor, Reflector, TodoManager) in an iterative loop. Follow TDD approach.

## Working Result
- Orchestrator class implemented with automated iteration loop
- Integrates TaskPlanner, Executor, Reflector, TodoManager, ToolRegistry
- Supports max_iterations limit and convergence detection
- Comprehensive tests with mock tools
- All tests passing

## Validation
- [ ] orchestrator.py implements Orchestrator class (~150 LOC as per DESIGN.md)
- [ ] __init__(goal, max_iterations, registry) initializes components
- [ ] run() method executes automated loop: plan → execute → reflect
- [ ] Reflection triggered every N iterations (start with N=3 as per DESIGN.md)
- [ ] Loop terminates on: reflection.done==True OR max_iterations reached
- [ ] Returns AgentRunResult with aggregated output
- [ ] Tests cover: successful completion, max iterations limit, error handling
- [ ] `uv run pytest nanoagent/core/orchestrator_test.py` passes
- [ ] `uv run ruff check` passes

## LLM Prompt
<prompt>
**Goal:** Automate the orchestration loop proven in M1 Task 007 integration test (converts manual POC to automated system)

**Constraints:**
- Must follow TDD: write tests before implementation
- Must match DESIGN.md § Orchestrator architecture
- Target ~150 LOC for implementation
- Must use M1 components as-is (no modifications to agents)
- Must support configurable reflection frequency

**Implementation Guidance:**
- Review M1 Task 007 integration test (nanoagent/tests/integration/orchestration_test.py) to understand proven pattern
- Reference DESIGN.md § Data Flow for loop structure
- Core class structure:
  ```python
  class Orchestrator:
      def __init__(self, goal: str, max_iterations: int = 10):
          self.goal = goal
          self.max_iterations = max_iterations
          self.todo = TodoManager()
          self.registry = ToolRegistry()
          self.context: Dict[str, str] = {}
          self.iteration = 0

      async def run(self) -> AgentRunResult:
          # Loop 0: Initial planning
          # Loop N: Execute + Reflect
          # Finalization: Synthesize results
  ```
- Main loop pattern (from DESIGN.md § Data Flow):
  1. Initial planning: call plan_tasks(goal), add to TodoManager
  2. Execution loop:
     - Get next task from TodoManager
     - Execute with executor
     - Store result in context
     - Every 3 iterations OR when no pending tasks: call reflector
     - Update TodoManager based on reflection
     - Check termination: reflection.done OR max_iterations
  3. Finalization: aggregate context into final output
- Write tests first:
  - Test complete orchestration cycle
  - Test max_iterations termination
  - Test reflection.done termination
  - Test context preservation through iterations
- Add ABOUTME comments
- Use M1 proven patterns for agent calls and context building

**M1 Learnings to Apply:**
- Context dict pattern: {task_id: result_output}
- Reflection trigger: every 3 iterations worked well
- Agent calls: use plan_tasks(), execute_task(), reflect_on_progress() from M1
- Error handling: comprehensive validation from M1 agents

**Validation:**
- Run `uv run pytest nanoagent/core/orchestrator_test.py` - all tests pass
- Run `uv run ruff check` - no errors
- Verify LOC count ~150 LOC
- Ensure no regressions in M1 tests
</prompt>

## Notes

**planning:** This is the core M2 deliverable - automating what we proved manually in M1 Task 007. The integration test from M1 provides the blueprint. Keep the loop simple: plan once, execute tasks, reflect periodically. M1 showed reflection every 3 iterations works well. Defer streaming to StreamManager (Task 011). Focus on correctness and reliability.
