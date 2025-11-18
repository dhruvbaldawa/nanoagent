# Task 012: End-to-End Tests for Multiple Goal Types

**Iteration:** Integration
**Status:** Pending
**Dependencies:** 008, 009, 010, 011 (Complete M2 system)
**Files:** nanoagent/tests/integration/e2e_test.py

## Description
Create comprehensive end-to-end tests validating the complete orchestration system works for multiple diverse goal types. Tests should use real LLM calls (like M1) and validate the system converges correctly. Follow TDD approach.

## Working Result
- End-to-end test file with 3+ diverse goal scenarios
- Tests validate: planning → execution → reflection → convergence
- All scenarios complete successfully with real LLM calls
- Comprehensive assertions on outputs
- All tests passing

## Validation
- [ ] e2e_test.py implements 3+ end-to-end test scenarios
- [ ] Test scenarios cover diverse goal types (calculation, multi-step reasoning, iterative refinement)
- [ ] Each test validates complete orchestration cycle end-to-end
- [ ] Tests use real LLM calls (require_real_api_key fixture)
- [ ] Assertions verify: AgentRunResult structure, goal completion, iteration limits
- [ ] `uv run pytest nanoagent/tests/integration/e2e_test.py` passes (with API key)
- [ ] Tests skip gracefully without API key
- [ ] `uv run ruff check` passes

## LLM Prompt
<prompt>
**Goal:** Validate M2 orchestration system works end-to-end for multiple diverse goal types (MILESTONE 2 VALIDATION)

**Constraints:**
- Must follow TDD: write tests before full integration
- Use real LLM calls (no mocking of agents)
- Must validate 3+ diverse goal types
- Must prove system converges correctly
- Must validate against M2 success criteria

**Implementation Guidance:**
- Reference M1 Task 007 integration test pattern for structure
- Use require_real_api_key fixture from conftest.py
- Test scenarios (diverse goal types):
  1. **Simple Calculation**: "Calculate the sum of squares of numbers 1 through 5"
     - Should complete in 1-2 iterations
     - Validates basic planning → execution → completion
  2. **Multi-Step Reasoning**: "What is 15% of 240, then multiply that result by 3?"
     - Should complete in 2-3 iterations
     - Validates task decomposition and result chaining
  3. **Iterative Refinement**: "Find the prime numbers between 20 and 30, then sum them"
     - Should complete in 2-4 iterations
     - Validates reflection detects missing steps and adds tasks
- Test structure:
  ```python
  @pytest.mark.asyncio
  async def test_e2e_simple_calculation(require_real_api_key):
      orchestrator = Orchestrator(goal="Calculate...", max_iterations=5)
      register_builtin_tools(orchestrator.registry)

      result = await orchestrator.run()

      assert isinstance(result, AgentRunResult)
      assert result.status == "completed"
      assert "result" in result.output.lower()
      # More specific assertions based on goal
  ```
- Assertions to validate:
  - AgentRunResult structure correct
  - status is "completed" (not "incomplete")
  - output contains expected information
  - Converged within max_iterations
- Use capsys to verify StreamManager events emitted
- Add ABOUTME comments

**Success Criteria (M2 Validation):**
- All 3+ goal types complete successfully
- System converges within reasonable iterations
- Outputs are coherent and goal-aligned
- No crashes or unhandled exceptions

**Validation:**
- Run `uv run pytest nanoagent/tests/integration/e2e_test.py` - all tests pass
- Run `uv run ruff check` - no errors
- If tests pass: M2 complete, ready for M3 planning
</prompt>

## Notes

**planning:** CRITICAL M2 VALIDATION. This proves the complete system works end-to-end with real LLMs. Similar to M1 Task 007, but now with automated orchestration and multiple goal types. If these tests pass, we've proven M2 integration works and can proceed to M3 hardening. Goal diversity is key - need to test different reasoning patterns to validate robustness.
