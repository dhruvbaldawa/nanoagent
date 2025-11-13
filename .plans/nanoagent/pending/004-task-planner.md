# Task 004: TaskPlanner Agent with Tests

**Iteration:** Foundation
**Status:** Pending
**Dependencies:** 002
**Files:** nanoagent/core/task_planner.py, nanoagent/core/task_planner_test.py

## Description
Implement TaskPlanner as a Pydantic AI agent that decomposes goals into tasks. Follow TDD: write tests validating structured output parsing first. This is a CRITICAL RISK validation - proves Pydantic AI structured outputs work. Target ~50 LOC.

## Working Result
- TaskPlanner agent configured with Pydantic AI
- Returns TaskPlanOutput with 3-7 tasks
- Tests validate structured output parsing with real LLM calls
- Tests cover: simple goals, ambiguous goals, structured output validation
- All tests passing (proves Critical Risk #1)

## Validation
- [ ] task_planner_test.py has tests calling real agent
- [ ] Tests validate TaskPlanOutput structure is correctly parsed
- [ ] Agent produces 3-7 tasks for typical goals
- [ ] Questions list works for ambiguous goals
- [ ] `uv run test nanoagent/core/task_planner_test.py` passes (may use real API)
- [ ] `uv run check` passes

## LLM Prompt
<prompt>
**Goal:** Prove that Pydantic AI can reliably produce structured TaskPlanOutput (validates Critical Risk #1)

**Constraints:**
- Must use REAL LLM calls in tests (no mocking)
- Must follow TDD: write tests before implementation
- Target ~50 LOC for implementation
- Must return TaskPlanOutput with 3-7 tasks for clear goals
- Must handle ambiguous goals (ask clarifying questions)
- Use anthropic:claude-sonnet-4-0 model

**Implementation Guidance:**
- Write tests first that call agent with various goal types
- Create Pydantic AI Agent with result_type=TaskPlanOutput
- Define clear system_prompt that explains task decomposition behavior
- Validate structured output parsing works reliably
- Test simple goals (should return tasks, no questions)
- Test ambiguous goals (may return questions)
- Test output structure always matches TaskPlanOutput schema
- Requires ANTHROPIC_API_KEY environment variable
- Add ABOUTME comments

**Critical Test Pattern:**
```python
@pytest.mark.asyncio
async def test_planner_simple_goal():
    result = await task_planner.run("Clear goal here")
    assert isinstance(result.data, TaskPlanOutput)
    assert 3 <= len(result.data.tasks) <= 7
    # Proves structured output works!
```

**System Prompt Guidance:**
- Explain when to return tasks vs. questions
- Emphasize specific, actionable task descriptions
- Request 3-7 tasks for clear goals
- Ask clarifying questions for ambiguous goals

**Validation:**
- Tests call real agent and pass
- Structured outputs parse correctly (Critical Risk #1 validated)
- Run `uv run check` - no errors
- If tests fail: architecture needs revision
</prompt>

## Notes

**planning:** This is the MOST CRITICAL task in Milestone 1. If Pydantic AI structured outputs don't work reliably, the entire approach fails. Tests with real LLM calls prove this risk is managed. Don't mock the LLM - we need to validate the real behavior.
