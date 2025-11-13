# Task 006: Reflector Agent with Gap Detection Tests

**Iteration:** Foundation
**Status:** Pending
**Dependencies:** 002, 003
**Files:** nanoagent/core/reflector.py, nanoagent/core/reflector_test.py

## Description
Implement Reflector as a Pydantic AI agent that evaluates progress and identifies gaps. Follow TDD: write tests with sample completed/pending tasks first. Validates ReflectionOutput parsing and gap detection logic. Target ~60 LOC.

## Working Result
- Reflector agent configured with Pydantic AI
- Returns ReflectionOutput with done status, gaps, new_tasks, complete_ids
- Tests validate gap identification with various scenarios
- Tests prove reflection quality (Critical Risk #3)
- All tests passing

## Validation
- [ ] reflector_test.py has tests with sample task histories
- [ ] Tests validate ReflectionOutput structure parsing
- [ ] Reflector identifies missing information correctly
- [ ] Reflector suggests relevant new tasks
- [ ] Reflector marks tasks complete appropriately
- [ ] `uv run test nanoagent/core/reflector_test.py` passes
- [ ] `uv run check` passes

## LLM Prompt
<prompt>
**Goal:** Prove that Reflector can identify missing information and suggest actionable next steps (validates Critical Risks #1 and #3)

**Constraints:**
- Must follow TDD: write tests before implementation
- Target ~60 LOC for implementation
- Must use real LLM calls in tests
- Must validate ReflectionOutput structure parsing
- Must test with various goal completion scenarios
- Pure reasoning agent (no tools)
- Use anthropic:claude-sonnet-4-0 model

**Implementation Guidance:**
- Write tests first with sample goal/task scenarios
- Create Pydantic AI Agent with result_type=ReflectionOutput
- System prompt should explain reflection analysis process
- Test: recognizes completed goals correctly (done=True)
- Test: identifies gaps when information missing
- Test: suggests actionable new tasks to fill gaps
- Test: output structure always matches ReflectionOutput
- Consider various goal types: simple vs. complex, clear vs. ambiguous
- Add ABOUTME comments

**Test Scenarios to Cover:**
- Simple completed goal (should return done=True, no new tasks)
- Partially completed goal (should identify gaps, suggest new tasks)
- Goal with pending tasks (should recognize what's already planned)
- Output structure validation (has all required fields)

**System Prompt Guidance:**
- Explain the four analysis questions (from DESIGN.md):
  1. Is goal fully accomplished? (done flag)
  2. What critical information is missing? (gaps list)
  3. What new tasks would fill those gaps? (new_tasks list)
  4. Which pending tasks are now irrelevant? (complete_ids list)
- Emphasize being thorough but concise
- Focus on what's missing, not what's been done

**Validation:**
- Tests prove reflection makes sensible decisions
- ReflectionOutput parsing works (Critical Risk #1 validated)
- Gap identification works (Critical Risk #3 validated)
- Run `uv run check` - no errors
</prompt>

## Notes

**planning:** This validates Critical Risk #3 (Reflection Loop Quality). Tests must prove the reflector makes good decisions about completion and gaps. This is a pure reasoning agent - no tools needed.
