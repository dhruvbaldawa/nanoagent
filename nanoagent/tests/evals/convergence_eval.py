# ABOUTME: Eval tests for convergence behavior dimension
# ABOUTME: Validates agent convergence toward goal through iterations

from typing import Any

import pytest

from nanoagent.evals.judge import evaluate
from nanoagent.evals.models import EvalDimension
from nanoagent.tests.evals.cases import CONVERGENCE_BEHAVIOR_CASES


@pytest.mark.eval
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "case",
    CONVERGENCE_BEHAVIOR_CASES,
    ids=[c["name"] for c in CONVERGENCE_BEHAVIOR_CASES],  # type: ignore[arg-type]
)
async def test_convergence_behavior(case: dict[str, Any], require_real_api_key: None) -> None:
    """Test convergence behavior evaluation with real LLM calls.

    Validates that the agent converges toward goal efficiently through
    planning, execution, and reflection iterations.
    """
    iteration_summary = case["iteration_summary"]

    eval_prompt = f"""Iteration Summary:
{iteration_summary}

Assess the agent's convergence toward the goal. Consider:
- Does progress increase each iteration?
- Are identified gaps being addressed?
- Is the agent moving toward the goal efficiently?
- What is the overall convergence quality?"""

    # Evaluate convergence behavior with LLM judge
    score = await evaluate(EvalDimension.CONVERGENCE_BEHAVIOR, eval_prompt)

    # Check score meets pass threshold
    if not score.passed:
        msg = f"Convergence behavior score {score.score}/5: {score.reasoning}"
        raise AssertionError(msg)
