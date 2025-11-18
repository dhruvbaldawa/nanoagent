# Task 008: Tool Registry for Pluggable Tools

**Iteration:** Integration
**Status:** Pending
**Dependencies:** 005 (Executor agent must support tool calling)
**Files:** nanoagent/tools/registry.py, nanoagent/tools/registry_test.py

## Description
Implement ToolRegistry class for managing pluggable tools. Provides registration, lookup, and listing capabilities. Simple dict-based storage with callable functions. Follow TDD: write tests first.

## Working Result
- ToolRegistry class implemented with register(), get(), list_names() methods
- Supports registering any callable (sync or async functions)
- Comprehensive tests covering registration, lookup, errors
- All tests passing

## Validation
- [ ] registry.py implements ToolRegistry with dict-based storage
- [ ] register(name, func) adds tools to registry
- [ ] get(name) retrieves registered tools (raises KeyError if missing)
- [ ] list_names() returns list of registered tool names
- [ ] Tests cover: registration, retrieval, missing tools, duplicate names
- [ ] `uv run pytest nanoagent/tools/` passes
- [ ] `uv run ruff check` passes

## LLM Prompt
<prompt>
**Goal:** Implement simple, reliable tool registry for pluggable tool management (validates M2 Integration risk)

**Constraints:**
- Must follow TDD: write tests before implementation
- Keep it simple: dict-based storage, no complex patterns
- Support both sync and async callables
- Must match DESIGN.md architecture (~30 LOC target)
- No database or persistence (in-memory only for M2)

**Implementation Guidance:**
- Reference DESIGN.md § ToolRegistry for architecture
- Simple class with:
  ```python
  class ToolRegistry:
      def __init__(self):
          self.tools: Dict[str, Callable] = {}

      def register(self, name: str, func: Callable) -> None:
          # Add tool to registry

      def get(self, name: str) -> Callable:
          # Retrieve tool (raise KeyError if missing)

      def list_names(self) -> List[str]:
          # Return list of tool names
  ```
- Write tests first:
  - Test registration and retrieval
  - Test get() raises KeyError for missing tools
  - Test list_names() returns correct names
  - Test can register both sync and async functions
- Add ABOUTME comments
- Keep implementation simple and readable

**Validation:**
- Run `uv run pytest nanoagent/tools/` - all tests pass
- Run `uv run ruff check` - no errors
- Verify LOC count stays within budget (~30 LOC for implementation)
</prompt>

## Notes

**planning:** Simple dict-based registry. No complex plugin system needed for M2. This is a well-understood pattern from plan.md § Risk Analysis (Critical + Known). Keep it minimal - just register, get, list. No auto-discovery, no validation (tools are just callables). Can extend in M3 if needed.
