# Task 013: Comprehensive Edge Case Testing

**Iteration:** Polish
**Status:** Pending
**Dependencies:** 012 (M2 complete)
**Files:** nanoagent/tests/edge_cases/ (new directory), existing *_test.py files

## Description
Expand test coverage to handle edge cases and failure modes across all components. Focus on scenarios that could cause production issues: malformed inputs, API failures, timeout scenarios, resource exhaustion, and adversarial inputs.

## Working Result
- New test suite covering edge cases for all core components
- Tests for failure modes: API errors, timeouts, malformed LLM outputs, resource limits
- Tests for adversarial inputs: injection attempts, very long inputs, special characters
- All edge cases handled gracefully with proper error messages
- Test coverage remains >80% with edge cases included
- All tests passing (202+ tests)

## Validation
- [ ] edge_cases/ directory created with organized test files
- [ ] Edge case tests for Orchestrator: max iterations, empty goal, no tasks, reflection failures
- [ ] Edge case tests for TaskPlanner: malformed output recovery, clarifying questions handling
- [ ] Edge case tests for Executor: tool failures, missing tools, invalid tool args
- [ ] Edge case tests for Reflector: empty context, all tasks failed, infinite loop detection
- [ ] Edge case tests for TodoManager: duplicate IDs, invalid priorities, empty queue operations
- [ ] Edge case tests for ToolRegistry: duplicate registration, missing tools, tool exceptions
- [ ] Edge case tests for security: expression injection, path traversal attempts, code injection
- [ ] All new tests pass: `uv run pytest nanoagent/tests/edge_cases/`
- [ ] Full test suite passes: `uv run pytest` (220+ tests expected)
- [ ] `uv run ruff check` passes

## LLM Prompt
<prompt>
**Goal:** Ensure production readiness by testing edge cases and failure modes across all components

**Constraints:**
- Must follow TDD: write failing tests first
- Tests should cover realistic failure scenarios
- Error messages must be clear and actionable
- No changes to core logic unless fixing actual bugs
- Maintain >80% test coverage

**Implementation Guidance:**

1. **Create test organization:**
   ```
   nanoagent/tests/edge_cases/
   ├── __init__.py
   ├── orchestrator_edge_test.py
   ├── agents_edge_test.py
   ├── tools_edge_test.py
   └── security_edge_test.py
   ```

2. **Critical edge cases to test:**

   **Orchestrator Edge Cases:**
   - Empty or whitespace-only goal (should raise ValueError)
   - Max iterations = 1 (should handle gracefully)
   - TaskPlanner returns empty task list (should complete immediately)
   - All tasks fail execution (should mark incomplete)
   - Reflection never sets done=True (should respect max_iterations)
   - Tool registry is empty (executor should handle gracefully)

   **Agent Edge Cases (TaskPlanner, Executor, Reflector):**
   - API timeout or rate limit errors (should retry with backoff)
   - Malformed LLM output that doesn't match schema (should retry)
   - Empty input strings (should validate and raise clear errors)
   - Very long inputs (>100k chars) (should truncate or reject)
   - Invalid dependencies in reflection output (should ignore)

   **Tool Edge Cases:**
   - Tool raises exception (should catch and return error message)
   - Tool returns None or invalid type (should handle gracefully)
   - Calculator with division by zero (should return error)
   - Expression evaluator with syntax error (should return error)
   - Missing tool called by executor (should fail task with clear message)

   **Security Edge Cases:**
   - Expression injection attempts: `__import__('os').system('ls')`
   - Path traversal in tool names: `../../etc/passwd`
   - Very large task descriptions (>1MB) (should reject)
   - Recursive task generation (reflection adds same tasks repeatedly)

3. **Test patterns to follow:**
   ```python
   @pytest.mark.asyncio
   async def test_orchestrator_empty_goal():
       """Empty goal should raise ValueError with clear message."""
       with pytest.raises(ValueError, match="Goal cannot be empty"):
           Orchestrator(goal="", max_iterations=10)

   @pytest.mark.asyncio
   async def test_executor_tool_exception():
       """Tool exceptions should be caught and returned as error messages."""
       registry = ToolRegistry()
       registry.register("failing_tool", lambda x: 1/0)  # ZeroDivisionError

       result = await execute_task(
           task_description="Use failing_tool",
           context={},
           registry=registry
       )

       assert not result.success
       assert "error" in result.output.lower()
   ```

4. **Use existing fixtures from conftest.py:**
   - Use pytest fixtures for common setups
   - Skip tests requiring API calls if ALLOW_MODEL_REQUESTS not set
   - Use mocking for LLM calls in edge case tests (focus on error handling, not LLM behavior)

5. **Bug fixes if needed:**
   - If tests reveal actual bugs, fix them in the core components
   - Document what was fixed in the Notes section
   - Ensure fixes don't break existing 202 tests

**Validation:**
- Run `uv run pytest nanoagent/tests/edge_cases/` - all new tests pass
- Run `uv run pytest` - full suite passes (220+ tests expected)
- Run `uv run ruff check` - no errors
- Review error messages - all should be clear and actionable
</prompt>

## Notes

**planning:** CRITICAL for production readiness. M1 and M2 focused on happy path validation. M3 must prove the system handles failures gracefully. Focus on realistic failure scenarios that could happen in production: API errors, malformed outputs, resource limits, adversarial inputs. Testing edge cases often reveals architectural weaknesses - be prepared to refactor if needed, but keep changes minimal. The 202 existing tests must continue passing.
