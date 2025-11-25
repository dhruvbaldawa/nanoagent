# Task 006: Verify Test Performance and Clean Up

## Objective
Verify all tests pass in <1s and clean up any remaining `require_real_api_key` references.

## Context
- Final task in Tier 1 implementation
- All previous tasks should have converted individual test files
- This task validates the complete migration

## Implementation

### Steps
1. Run full test suite and verify timing: `pytest nanoagent/ -v --durations=10`
2. Verify no `require_real_api_key` references remain in test files (keep fixture definition in conftest.py for future Tier 2 use)
3. Verify no API calls are made (check for any `ANTHROPIC_API_KEY` or `OPENROUTER_API_KEY` access warnings)
4. Document any test failures and fix

### Verification Commands
```bash
# Run all tests with timing
pytest nanoagent/ -v --durations=10

# Check for remaining require_real_api_key usage (should only be in conftest.py)
grep -r "require_real_api_key" nanoagent/ --include="*_test.py"

# Verify total test count
pytest nanoagent/ --collect-only | tail -5
```

## LLM Prompt

```
Final verification for Tier 1 eval-framework implementation.

Run the test suite and verify:
1. All tests pass
2. Total execution time is <1s
3. No API calls are made
4. No require_real_api_key references in *_test.py files (fixture stays in conftest.py)

If any tests fail, investigate and fix the root cause.
Report the final test count and execution time.
```

## Success Criteria
- [ ] `pytest nanoagent/` completes in <1s
- [ ] 100% test pass rate
- [ ] No `require_real_api_key` in test files (only in conftest.py)
- [ ] No API call warnings or errors

## Files
- Various test files (verify only)
- `nanoagent/conftest.py` (keep fixture for future Tier 2)

## Estimated LOC: ~0 (verification only)
