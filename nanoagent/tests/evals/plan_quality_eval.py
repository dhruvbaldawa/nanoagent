# ABOUTME: Eval tests for plan quality dimension
# ABOUTME: Validates task planning quality using LLM-as-judge

from typing import Any

import pytest

from nanoagent.core.task_planner import plan_tasks
from nanoagent.evals.judge import evaluate
from nanoagent.evals.models import EvalDimension
from nanoagent.tests.evals.cases import PLAN_QUALITY_CASES


@pytest.mark.eval
@pytest.mark.asyncio
@pytest.mark.parametrize("case", PLAN_QUALITY_CASES, ids=[c["name"] for c in PLAN_QUALITY_CASES])  # type: ignore[arg-type]
async def test_plan_quality(case: dict[str, Any], require_real_api_key: None) -> None:
    """Test plan quality evaluation with real LLM calls.

    Validates that the task planner produces high-quality plans that decompose
    goals appropriately, and that the LLM-as-judge can correctly evaluate them.
    """
    # Generate plan from goal
    plan = await plan_tasks(case["goal"])
    if plan is None:
        msg = f"plan_tasks returned None for goal: {case['goal']}"
        raise AssertionError(msg)

    # Build evaluation prompt from plan
    tasks_str = "\n".join([f"- {task}" for task in plan.tasks]) if plan.tasks else "No tasks identified"
    questions_str = "\n".join([f"- {q}" for q in plan.questions]) if plan.questions else "No questions"

    eval_prompt = f"""Goal: {case["goal"]}

Tasks:
{tasks_str}

Clarifying Questions:
{questions_str}"""

    # Evaluate plan quality with LLM judge
    score = await evaluate(EvalDimension.PLAN_QUALITY, eval_prompt)

    # Check score meets pass threshold
    if not score.passed:
        msg = f"Plan quality score {score.score}/5: {score.reasoning}"
        raise AssertionError(msg)
