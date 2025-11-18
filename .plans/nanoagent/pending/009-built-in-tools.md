# Task 009: Built-in Tools for Testing

**Iteration:** Integration
**Status:** Pending
**Dependencies:** 008 (ToolRegistry)
**Files:** nanoagent/tools/builtin.py, nanoagent/tools/builtin_test.py

## Description
Implement minimal set of built-in tools for M2 testing. Start with simple mock tools (calculator, echo) to validate tool registry and executor integration. Follow TDD approach.

## Working Result
- builtin.py with 2-3 simple tools implemented
- Tools registered via register_builtin_tools(registry) function
- Comprehensive tests for each tool
- All tests passing

## Validation
- [ ] builtin.py implements 2-3 simple tools (e.g., calculator, echo, get_timestamp)
- [ ] register_builtin_tools(registry: ToolRegistry) function auto-registers all tools
- [ ] Each tool has proper async signature and error handling
- [ ] Tests cover normal cases and error cases for each tool
- [ ] Tools work with ToolRegistry.get()
- [ ] `uv run pytest nanoagent/tools/` passes
- [ ] `uv run ruff check` passes

## LLM Prompt
<prompt>
**Goal:** Implement minimal built-in tools for validating M2 orchestration (keep simple, can expand in M3)

**Constraints:**
- Must follow TDD: write tests before implementation
- Keep it minimal: 2-3 simple tools only
- All tools must be async functions
- Must match DESIGN.md patterns
- Target ~50-80 LOC for implementation (not the full ~100 LOC planned - deferring complex tools to M3)

**Implementation Guidance:**
- Simple tools for M2 validation:
  1. `mock_calculator(expression: str) -> str` - Evaluates simple math (use eval for testing only)
  2. `echo(message: str) -> str` - Returns the message
  3. Optional: `get_timestamp() -> str` - Returns current timestamp
- Example tool pattern:
  ```python
  async def mock_calculator(expression: str) -> str:
      \"\"\"Evaluates simple math expressions (testing only).\"\"\"
      try:
          result = eval(expression)  # Safe for controlled testing
          return f"Result: {result}"
      except Exception as e:
          return f"Error: {str(e)}"
  ```
- Provide `register_builtin_tools(registry: ToolRegistry)` function to auto-register
- Write tests first for each tool:
  - Test normal operation
  - Test error handling
  - Test registration via register_builtin_tools()
- Add ABOUTME comments
- Keep implementation simple

**Deferred to M3:**
- Real web_search tool
- File operations (read_file, write_file)
- Code execution tool
- API call tool

**Validation:**
- Run `uv run pytest nanoagent/tools/` - all tests pass
- Run `uv run ruff check` - no errors
- Verify tools work with ToolRegistry
</prompt>

## Notes

**planning:** Keeping M2 tools minimal to focus on orchestration validation. Mock tools are sufficient to prove the system works. Can add real tools (web search, file ops, etc.) in M3 when we have proven the orchestration loop. This reduces M2 scope and keeps us within LOC budget.
