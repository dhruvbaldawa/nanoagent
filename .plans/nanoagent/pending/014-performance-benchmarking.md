# Task 014: Performance Benchmarking and Validation

**Iteration:** Polish
**Status:** Pending
**Dependencies:** 013 (Edge cases handled)
**Files:** nanoagent/benchmarks/ (new directory), nanoagent/core/performance.py (new)

## Description
Create performance benchmarking infrastructure to measure and validate system performance against success criteria. Track key metrics: iterations to completion, token usage, API call count, execution time. Validate that system converges efficiently for different goal types.

## Working Result
- Performance benchmarking script measuring key metrics
- Benchmark results for 10+ diverse goals documented
- Performance metrics module for runtime tracking
- Validation that system meets efficiency criteria:
  - Simple goals: <5 iterations, <10k tokens
  - Complex goals: <15 iterations, <50k tokens
  - No infinite loops (respects max_iterations)
- Performance documentation in benchmarks/RESULTS.md
- All tests passing

## Validation
- [ ] benchmarks/ directory created with benchmark scripts
- [ ] performance.py module tracks: iterations, tokens, API calls, execution time
- [ ] Benchmark script runs 10+ diverse goals and measures performance
- [ ] RESULTS.md documents benchmark findings with analysis
- [ ] Performance metrics integrated into Orchestrator (optional runtime tracking)
- [ ] Validation against success criteria:
  - [ ] Simple calculation goals complete in <5 iterations
  - [ ] Multi-step reasoning goals complete in <15 iterations
  - [ ] Token usage reasonable (<50k for complex goals)
  - [ ] No performance regressions from M2 baseline
- [ ] Benchmark script: `uv run python nanoagent/benchmarks/run_benchmarks.py`
- [ ] All tests still pass: `uv run pytest`
- [ ] `uv run ruff check` passes

## LLM Prompt
<prompt>
**Goal:** Measure and validate system performance to ensure production efficiency

**Constraints:**
- Must not break existing functionality
- Benchmarks should be reproducible
- Track metrics that matter for production use
- Document baseline performance for future comparison
- Keep benchmark code separate from core framework

**Implementation Guidance:**

1. **Create performance tracking module (nanoagent/core/performance.py):**
   ```python
   # ABOUTME: Performance metrics tracking for orchestration runs
   # ABOUTME: Measures iterations, token usage, API calls, and execution time

   from dataclasses import dataclass, field
   from datetime import datetime
   from typing import List

   @dataclass
   class PerformanceMetrics:
       """Tracks performance metrics for an orchestration run."""
       goal: str
       start_time: datetime = field(default_factory=datetime.now)
       end_time: datetime | None = None
       iterations: int = 0
       api_calls: int = 0
       tokens_used: int = 0  # Approximate
       tasks_completed: int = 0
       tasks_total: int = 0
       status: str = "running"

       def duration_seconds(self) -> float:
           """Calculate duration in seconds."""
           if self.end_time:
               return (self.end_time - self.start_time).total_seconds()
           return 0.0

       def to_dict(self) -> dict:
           """Convert to dictionary for serialization."""
           return {
               "goal": self.goal,
               "duration_seconds": self.duration_seconds(),
               "iterations": self.iterations,
               "api_calls": self.api_calls,
               "tokens_used": self.tokens_used,
               "tasks_completed": self.tasks_completed,
               "tasks_total": self.tasks_total,
               "status": self.status,
           }
   ```

2. **Create benchmark script (nanoagent/benchmarks/run_benchmarks.py):**
   - Test goals covering different complexity levels:
     - **Simple**: "What is 5 + 3?"
     - **Medium**: "Calculate the sum of squares from 1 to 10"
     - **Complex**: "Find prime numbers between 1 and 50, then sum them"
     - **Multi-step**: "Calculate 15% of 360, multiply by 2, then subtract 50"
     - **Iterative**: "Count from 1 to 5, squaring each number"
   - Run each goal and collect metrics
   - Output results as JSON and human-readable table
   - Save to benchmarks/RESULTS.md with analysis

3. **Benchmark script structure:**
   ```python
   import asyncio
   import json
   from datetime import datetime
   from nanoagent.core.orchestrator import Orchestrator
   from nanoagent.tools.builtin import register_builtin_tools

   BENCHMARK_GOALS = [
       ("Simple", "What is 5 + 3?"),
       ("Medium", "Calculate the sum of squares from 1 to 10"),
       # ... more goals
   ]

   async def run_single_benchmark(category: str, goal: str) -> dict:
       """Run single benchmark and collect metrics."""
       orchestrator = Orchestrator(goal=goal, max_iterations=20)
       register_builtin_tools(orchestrator.registry)

       start = datetime.now()
       result = await orchestrator.run()
       end = datetime.now()

       return {
           "category": category,
           "goal": goal,
           "status": result.status,
           "duration_seconds": (end - start).total_seconds(),
           "iterations": orchestrator.iteration,
           # Approximate token usage from output length
           "approx_tokens": len(result.output) // 4,
       }

   async def main():
       results = []
       for category, goal in BENCHMARK_GOALS:
           print(f"Running: {category} - {goal[:50]}...")
           result = await run_single_benchmark(category, goal)
           results.append(result)
           print(f"  → {result['status']} in {result['iterations']} iterations")

       # Save results
       with open("nanoagent/benchmarks/results.json", "w") as f:
           json.dump(results, f, indent=2)

       # Generate RESULTS.md
       generate_results_markdown(results)

   if __name__ == "__main__":
       asyncio.run(main())
   ```

4. **Generate RESULTS.md with analysis:**
   - Table of benchmark results
   - Analysis of performance patterns
   - Validation against success criteria
   - Recommendations for optimization (if needed)

5. **Optional: Integrate metrics into Orchestrator:**
   - Add optional performance tracking to Orchestrator
   - Emit performance metrics via StreamManager
   - Keep it simple - don't over-engineer

6. **Validation against success criteria:**
   - Simple goals should complete in <5 iterations
   - Complex goals should complete in <15 iterations
   - Token usage should be reasonable (<50k for complex)
   - No infinite loops or runaway iterations
   - Document any goals that don't meet criteria

**References:**
- See M2 Task 012 e2e_test.py for existing goal patterns
- Use existing Orchestrator API (don't modify core unless necessary)
- Keep benchmarks separate from production code

**Validation:**
- Run `uv run python nanoagent/benchmarks/run_benchmarks.py`
- Review benchmarks/RESULTS.md for analysis
- Verify all benchmarks complete successfully
- Run `uv run pytest` - all tests pass
- Run `uv run ruff check` - no errors
</prompt>

## Notes

**planning:** Performance validation is critical for production use. Need to establish baseline metrics and ensure system converges efficiently. This task is about measurement and documentation, not optimization. If performance is poor, document it and defer optimization. Focus on: (1) Can we measure performance? (2) Does system meet basic efficiency criteria? (3) Do we have baseline for future comparison? Keep it simple - don't add complex monitoring infrastructure yet.
