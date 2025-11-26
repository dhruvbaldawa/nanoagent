# Task 014: Validate evals and tune thresholds

## Goal
Run all eval tests with real LLM, validate pass rate, tune if needed.

## Context
- Final validation step for Tier 2
- Requires all previous tasks complete
- May need prompt or threshold adjustments

## Constraints
- >80% pass rate target (at least 7/9 cases)
- Runtime <5 minutes
- Cost <$0.50 per run

## Validation Steps
1. Run `pytest -m eval -v` with real LLM
2. Review scores and reasoning for each case
3. Identify patterns in failures
4. Tune pass_threshold or judge prompts if needed
5. Document results in plan.md

## Troubleshooting

**If pass rate too low:**
- Review dimension prompts for clarity
- Consider more specific evaluation criteria
- Lower pass_threshold to 2 if judge is strict

**If scores inconsistent:**
- Add examples to judge prompts
- Use more specific criteria
- Check model selection

## Validation
- [ ] All 9 eval tests run successfully
- [ ] Pass rate >80%
- [ ] Runtime <5 minutes
- [ ] Results documented

## Files
- `.plans/eval-framework/plan.md` (update with results)
