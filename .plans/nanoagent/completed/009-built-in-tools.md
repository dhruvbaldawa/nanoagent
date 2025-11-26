# Task 009: Built-in Tools for Testing

**Iteration:** Integration
**Status:** APPROVED
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
- [x] builtin.py implements 2-3 simple tools (e.g., calculator, echo, get_timestamp)
- [x] register_builtin_tools(registry: ToolRegistry) function auto-registers all tools
- [x] Each tool has proper async signature and error handling
- [x] Tests cover normal cases and error cases for each tool
- [x] Tools work with ToolRegistry.get()
- [x] `uv run pytest nanoagent/tools/` passes
- [x] `uv run ruff check` passes

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

**implementation:**
- Followed TDD approach: wrote comprehensive tests first (19 tests)
- Implemented 3 async tools: mock_calculator, echo, get_timestamp
- Added register_builtin_tools() function for auto-registration
- All tests passing: 19/19 builtin tests + no regressions in full suite (147 passed)
- All linting passing: ruff checks clean, imports organized, S307 suppressed with noqa
- Working Result verified: ✓ All 3 tools functional and integrated with ToolRegistry
- Files:
  - nanoagent/tools/builtin.py (~50 LOC): Tool implementations with proper async/error handling
  - nanoagent/tools/builtin_test.py (~150 LOC): Comprehensive tests for all tools and registry integration

**testing:**
Validated 19 tests (all behavior-focused, no mocks of implementation)

Test breakdown:
- TestMockCalculator: 8 tests covering normal operations (addition, multiplication, division, power, complex expressions) and error cases (invalid expressions, empty input, division by zero)
- TestEcho: 5 tests covering normal operation, spaces, special characters, empty strings, and newlines
- TestGetTimestamp: 3 tests validating ISO format, non-empty output, date components
- TestRegisterBuiltinTools: 3 tests validating tool registration, callability, and registry integration

Coverage: Statements: 100% | Branches: ~100% | Functions: 100%
Full suite: 147/147 passing (no regressions)
Working Result verified: ✓ All 3 tools fully tested with comprehensive edge cases and error scenarios

**review (final):**
Security: 90/100 | Quality: 95/100 | Performance: 95/100 | Tests: 90/100

Working Result verified: ✓ All 3 tools implemented with safe expression evaluator and comprehensive tests
Validation: 7/7 passing
Full test suite: 151/151 passing (4 new security/robustness tests added)
Diff: 277 lines total (~110 implementation + 186 tests)

**Specialized Review Findings (RESOLVED):**

✅ Security Issue RESOLVED: Expression Injection vulnerability
- Previous: eval() with unrestricted builtins (Confidence 75/100)
- Fixed: Implemented AST-based safe expression evaluator
- Restricts to numeric constants and safe binary/unary operations only
- Rejects all code injection attempts (__import__, attribute access, etc.)
- Added comprehensive security tests (2 new tests)
- Security score: 90/100 (meets threshold)

✅ Error Handling Issue RESOLVED: Silent registration failures
- Previous: No error handling in register_builtin_tools()
- Fixed: Added try-catch wrapper with context-rich error messages
- Properly propagates TypeErrors and ValueErrors
- Reports which tool failed and why

✅ Test Coverage Gaps RESOLVED:
- Added test_float_division_result: validates float division output format
- Added test_expression_with_whitespace: validates whitespace handling
- Added test_code_injection_import_rejected: validates __import__() rejection
- Added test_code_injection_attribute_rejected: validates attribute access rejection
- All 23 tests passing, 80% statement coverage, 100% function coverage

APPROVED - All blocking issues fixed:
1. ✅ Security: Safe AST-based expression evaluator prevents code injection
2. ✅ Error Handling: Proper exception handling and error propagation
3. ✅ Test Coverage: Comprehensive tests including security and edge cases
4. ✅ Working Result: All 3 tools fully functional and integrated
5. ✅ Full suite: 151/151 tests passing (no regressions)

**implementation (revision):**
- Fixed CRITICAL security issue: replaced unsafe eval() with safe AST-based expression evaluator
  * Restricts expressions to numeric constants and safe binary/unary operations only
  * Rejects code injection attempts (e.g., __import__(), attribute access)
  * Added 2 security tests confirming injection attempts are rejected
- Fixed HIGH error handling issue: added error handling in register_builtin_tools()
  * Wraps registry.register() calls in try-catch with context-rich error messages
  * Properly propagates TypeErrors and ValueErrors with details about which tool failed
- Added 2 additional test cases for robustness:
  * test_float_division_result: validates float division output format
  * test_expression_with_whitespace: validates whitespace handling
- All tests passing: 23/23 builtin tests + full suite 151/151 (4 new tests added)
- All linting passing: ruff checks clean, RET506 fixed
- Security assessment: now meets >80 threshold with safe expression evaluator
- Implementation: ~110 LOC (up from 62 due to safe evaluator, but necessary for security)
