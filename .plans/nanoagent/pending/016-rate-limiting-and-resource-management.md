# Task 016: Rate Limiting and Resource Management

**Iteration:** Polish
**Status:** Pending
**Dependencies:** 015 (Observability instrumentation)
**Files:** nanoagent/core/rate_limiter.py (new), nanoagent/core/orchestrator.py (enhance)

## Description
Implement production-ready rate limiting and resource management to prevent API abuse and runaway costs. Add configurable limits for: max iterations, max tasks, max API calls per time window, and execution timeout. Ensure graceful handling when limits are reached with clear error messages.

## Working Result
- RateLimiter module with sliding window rate limiting for API calls
- Resource limits configurable on Orchestrator (max_iterations, max_tasks, timeout)
- Budget enforcement via iteration/task limits (complementing OTEL token tracking)
- Graceful handling when limits reached (no crashes, clear error messages)
- Tests for all limit scenarios
- Documentation on production resource management
- All tests passing

## Validation
- [ ] rate_limiter.py module with sliding window rate limiter
- [ ] Rate limiter integrated into agent calls (planner, executor, reflector)
- [ ] Orchestrator supports: max_iterations (exists), max_tasks (new), timeout (new)
- [ ] Orchestrator enforces limits and returns clear error messages
- [ ] Tests for rate limit scenarios (under limit, at limit, exceeded)
- [ ] Tests for resource limit scenarios (max tasks, timeout)
- [ ] Documentation in DESIGN.md on resource management
- [ ] Example demonstrating rate limiting configuration
- [ ] All tests pass: `uv run pytest` (240+ tests expected)
- [ ] `uv run ruff check` passes

## LLM Prompt
<prompt>
**Goal:** Enable production resource management with rate limiting and configurable limits

**Constraints:**
- Must not break existing functionality (all 230+ tests must pass)
- Rate limiting should be optional (default: no limits for local dev)
- Limits should be enforced gracefully (no crashes, clear errors)
- Keep it simple - don't over-engineer
- Follow existing Orchestrator patterns

**Implementation Guidance:**

1. **Create rate limiter module (nanoagent/core/rate_limiter.py):**
   ```python
   # ABOUTME: Sliding window rate limiter for API call management
   # ABOUTME: Prevents API abuse and enforces configurable rate limits

   import time
   from collections import deque
   from dataclasses import dataclass


   @dataclass
   class RateLimiter:
       """
       Sliding window rate limiter for API calls.

       Tracks calls within a time window and enforces maximum rate.
       """

       max_calls: int  # Maximum calls allowed in window
       window_seconds: float  # Time window in seconds
       _calls: deque = None  # type: ignore

       def __post_init__(self):
           """Initialize calls queue."""
           self._calls = deque()

       def check_and_increment(self) -> bool:
           """
           Check if call is allowed and increment counter.

           Returns:
               True if call allowed, False if rate limit exceeded

           Raises:
               RuntimeError: If rate limit exceeded (configurable behavior)
           """
           now = time.time()

           # Remove calls outside window
           while self._calls and self._calls[0] < now - self.window_seconds:
               self._calls.popleft()

           # Check if we're at limit
           if len(self._calls) >= self.max_calls:
               return False

           # Record this call
           self._calls.append(now)
           return True

       def wait_if_needed(self) -> None:
           """
           Block until a call is allowed (for synchronous use).

           Waits until oldest call falls outside the window.
           """
           now = time.time()

           # Remove calls outside window
           while self._calls and self._calls[0] < now - self.window_seconds:
               self._calls.popleft()

           # If at limit, wait until oldest call expires
           if len(self._calls) >= self.max_calls:
               wait_time = (self._calls[0] + self.window_seconds) - now
               if wait_time > 0:
                   time.sleep(wait_time)
               self._calls.popleft()

           # Record this call
           self._calls.append(time.time())

       def remaining_calls(self) -> int:
           """Get number of calls remaining in current window."""
           now = time.time()
           # Remove expired calls
           while self._calls and self._calls[0] < now - self.window_seconds:
               self._calls.popleft()
           return max(0, self.max_calls - len(self._calls))
   ```

2. **Enhance Orchestrator with resource limits:**
   ```python
   # In orchestrator.py __init__:

   def __init__(
       self,
       goal: str,
       max_iterations: int = 10,
       max_tasks: int | None = None,  # NEW: Limit total tasks
       timeout_seconds: float | None = None,  # NEW: Execution timeout
       rate_limiter: RateLimiter | None = None,  # NEW: API rate limiter
       registry: ToolRegistry | None = None,
   ) -> None:
       # ... existing validation ...

       if max_tasks is not None and max_tasks <= 0:
           raise ValueError("max_tasks must be positive")

       if timeout_seconds is not None and timeout_seconds <= 0:
           raise ValueError("timeout_seconds must be positive")

       self.max_tasks = max_tasks
       self.timeout_seconds = timeout_seconds
       self.rate_limiter = rate_limiter
       self.start_time: float | None = None  # Set in run()
   ```

3. **Enforce limits in Orchestrator.run():**
   ```python
   # In run() method:

   async def run(self) -> AgentRunResult:
       """Run orchestration loop with resource limits."""
       self.start_time = time.time()

       try:
           # ... existing planning phase ...

           # Main execution loop
           while self.iteration < self.max_iterations:
               # Check timeout
               if self.timeout_seconds:
                   elapsed = time.time() - self.start_time
                   if elapsed > self.timeout_seconds:
                       return AgentRunResult(
                           output=self._synthesize_output(),
                           status=AgentStatus.INCOMPLETE,
                           reason=f"Execution timeout after {elapsed:.1f}s"
                       )

               # Check max tasks limit
               if self.max_tasks and len(self.context) >= self.max_tasks:
                   return AgentRunResult(
                       output=self._synthesize_output(),
                       status=AgentStatus.INCOMPLETE,
                       reason=f"Maximum tasks limit reached ({self.max_tasks})"
                   )

               # Check rate limit before API call
               if self.rate_limiter and not self.rate_limiter.check_and_increment():
                   # Wait for rate limit window (or fail fast)
                   self.rate_limiter.wait_if_needed()

               # ... rest of execution loop ...
   ```

4. **Add tests (rate_limiter_test.py):**
   ```python
   import time
   import pytest
   from nanoagent.core.rate_limiter import RateLimiter


   def test_rate_limiter_under_limit():
       """Calls under limit should be allowed."""
       limiter = RateLimiter(max_calls=3, window_seconds=1.0)

       assert limiter.check_and_increment()  # 1st call
       assert limiter.check_and_increment()  # 2nd call
       assert limiter.check_and_increment()  # 3rd call
       assert limiter.remaining_calls() == 0


   def test_rate_limiter_at_limit():
       """4th call should be rejected when limit is 3."""
       limiter = RateLimiter(max_calls=3, window_seconds=1.0)

       assert limiter.check_and_increment()  # 1st
       assert limiter.check_and_increment()  # 2nd
       assert limiter.check_and_increment()  # 3rd
       assert not limiter.check_and_increment()  # 4th - rejected


   def test_rate_limiter_sliding_window():
       """Old calls should expire after window."""
       limiter = RateLimiter(max_calls=2, window_seconds=0.5)

       assert limiter.check_and_increment()  # 1st
       assert limiter.check_and_increment()  # 2nd
       assert not limiter.check_and_increment()  # 3rd - rejected

       time.sleep(0.6)  # Wait for window to expire

       assert limiter.check_and_increment()  # Should succeed now


   def test_rate_limiter_wait_if_needed():
       """wait_if_needed should block until call allowed."""
       limiter = RateLimiter(max_calls=2, window_seconds=0.5)

       limiter.wait_if_needed()  # 1st - immediate
       limiter.wait_if_needed()  # 2nd - immediate

       start = time.time()
       limiter.wait_if_needed()  # 3rd - should wait ~0.5s
       elapsed = time.time() - start

       assert elapsed >= 0.4  # Allow some tolerance


   @pytest.mark.asyncio
   async def test_orchestrator_max_tasks_limit():
       """Orchestrator should respect max_tasks limit."""
       from nanoagent.core.orchestrator import Orchestrator
       from nanoagent.tools.builtin import register_builtin_tools

       orchestrator = Orchestrator(
           goal="Count from 1 to 100",
           max_iterations=50,
           max_tasks=5,  # Limit to 5 tasks
       )
       register_builtin_tools(orchestrator.registry)

       result = await orchestrator.run()

       assert result.status == "incomplete"
       assert "maximum tasks limit" in result.reason.lower()
       assert len(orchestrator.context) <= 5


   @pytest.mark.asyncio
   async def test_orchestrator_timeout():
       """Orchestrator should respect timeout."""
       from nanoagent.core.orchestrator import Orchestrator
       from nanoagent.tools.builtin import register_builtin_tools

       orchestrator = Orchestrator(
           goal="Complex goal requiring many iterations",
           max_iterations=100,
           timeout_seconds=2.0,  # 2 second timeout
       )
       register_builtin_tools(orchestrator.registry)

       start = time.time()
       result = await orchestrator.run()
       elapsed = time.time() - start

       assert elapsed < 5.0  # Should timeout before 100 iterations
       assert result.status == "incomplete"
       assert "timeout" in result.reason.lower()
   ```

5. **Create example (examples/rate_limiting_demo.py):**
   ```python
   """
   Rate limiting demo showing resource management in production.

   Demonstrates:
   - API rate limiting (max calls per time window)
   - Maximum task limit (budget control)
   - Execution timeout (prevent runaway execution)
   """

   import asyncio

   from nanoagent.core.orchestrator import Orchestrator
   from nanoagent.core.rate_limiter import RateLimiter
   from nanoagent.tools.builtin import register_builtin_tools


   async def main():
       # Configure rate limiter: max 10 API calls per minute
       rate_limiter = RateLimiter(max_calls=10, window_seconds=60.0)

       orchestrator = Orchestrator(
           goal="Calculate factorials from 1 to 10",
           max_iterations=20,
           max_tasks=15,  # Limit total tasks
           timeout_seconds=30.0,  # 30 second timeout
           rate_limiter=rate_limiter,
       )
       register_builtin_tools(orchestrator.registry)

       print(f"Goal: {orchestrator.goal}")
       print(f"Limits: {orchestrator.max_iterations} iterations, "
             f"{orchestrator.max_tasks} tasks, "
             f"{orchestrator.timeout_seconds}s timeout")
       print()

       result = await orchestrator.run()

       print(f"\nResult: {result.output}")
       print(f"Status: {result.status}")
       if result.status == "incomplete":
           print(f"Reason: {result.reason}")

       print(f"\nTasks completed: {len(orchestrator.context)}")
       print(f"Iterations: {orchestrator.iteration}")
       print(f"API calls remaining: {rate_limiter.remaining_calls()}")


   if __name__ == "__main__":
       asyncio.run(main())
   ```

6. **Update DESIGN.md:**
   - Add "Production Resource Management" section
   - Document rate limiting configuration
   - Document resource limits (max_tasks, timeout)
   - Document error handling when limits reached

**References:**
- Existing Orchestrator max_iterations pattern
- Task 015 for OTEL token tracking (complementary, not duplicate)

**Validation:**
- Run `uv run pytest nanoagent/core/rate_limiter_test.py` - tests pass
- Run `uv run python examples/rate_limiting_demo.py` - demo works
- Run `uv run pytest` - all tests pass (240+ total)
- Run `uv run ruff check` - no errors
</prompt>

## Notes

**planning:** Rate limiting and resource management are critical for production use. Need to prevent: (1) API abuse (rate limiting), (2) Runaway costs (max tasks), (3) Infinite loops (timeout). Keep it simple - sliding window rate limiter is straightforward and effective. Make limits optional (default: no limits for local dev). Graceful degradation - return AgentRunResult with status="incomplete" and clear reason when limits hit. This complements Task 015's OTEL token tracking (OTEL tracks what happened, this prevents bad things from happening).
