# Task 002: Data Models with Validation Tests

**Iteration:** Foundation
**Status:** Pending
**Dependencies:** 001
**Files:** nanoagent/models/schemas.py, nanoagent/models/schemas_test.py

## Description
Define all 5 Pydantic data models (Task, TaskPlanOutput, ExecutionResult, ReflectionOutput, AgentRunResult) with comprehensive validation tests. Follow TDD: write tests first for each model's validation rules.

## Working Result
- All 5 models defined with proper Pydantic validation
- Comprehensive tests covering valid cases, edge cases, and validation failures
- Tests validate required fields, optional fields, default values, and type constraints
- All tests passing

## Validation
- [ ] schemas.py contains all 5 models matching DESIGN.md
- [ ] schemas_test.py has tests for each model's validation
- [ ] Tests cover: valid inputs, missing required fields, invalid types, edge cases
- [ ] `uv run test nanoagent/models/` passes
- [ ] `uv run check` passes

## LLM Prompt
<prompt>
**Goal:** Implement type-safe data models that ensure reliable structured outputs from Pydantic AI agents (validates Critical Risk #1 at data layer)

**Constraints:**
- Must follow TDD: write tests before implementation
- All models must use Pydantic with proper validation
- Task IDs must be 8-character UUIDs
- Use Literal types for restricted values (e.g., status fields)
- Default values must match DESIGN.md specifications
- Tests must cover both valid and invalid inputs

**Models Required** (from DESIGN.md):
1. **Task**: id, description, status (pending/done/cancelled), priority (default: 5)
2. **TaskPlanOutput**: tasks (List[str]), questions (List[str], default: [])
3. **ExecutionResult**: success (bool), output (str)
4. **ReflectionOutput**: done (bool), gaps (List[str]), new_tasks (List[str]), complete_ids (List[str], default: [])
5. **AgentRunResult**: output (str), status (str)

**Implementation Guidance:**
- For each model: write failing tests first, then implement to make tests pass
- Test valid creation with defaults
- Test required fields enforcement (use pytest.raises)
- Test Literal type validation rejects invalid values
- Test list fields handle empty cases
- Test ID generation produces 8-character strings
- Test field customization when values provided
- Add ABOUTME comments explaining file purpose

**Test Pattern Example:**
```python
def test_model_creation_valid():
    instance = Model(required="value")
    assert instance.required == "value"
    assert instance.optional == default_value

def test_model_invalid_literal():
    with pytest.raises(ValueError):
        Model(status="invalid")
```

**Validation:**
- All 5 models defined in schemas.py
- Comprehensive test coverage in schemas_test.py
- Run `uv run test nanoagent/models/` - all tests pass
- Run `uv run check` - no linting or type errors
</prompt>

## Notes

**planning:** This is critical - all agent communication depends on these models working correctly. TDD ensures we catch validation issues early. Tests prove that Pydantic structured outputs will be reliable. This validates Critical Risk #1 (structured output reliability) at the data model level.
