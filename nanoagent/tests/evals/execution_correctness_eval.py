# ABOUTME: Eval tests for execution correctness dimension
# ABOUTME: Validates task execution success flag and output quality

from typing import Any

import pytest

from nanoagent.core.executor import execute_task
from nanoagent.evals.judge import evaluate
from nanoagent.evals.models import EvalDimension
from nanoagent.tests.evals.cases import EXECUTION_CORRECTNESS_CASES


@pytest.mark.eval
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "case",
    EXECUTION_CORRECTNESS_CASES,
    ids=[c["name"] for c in EXECUTION_CORRECTNESS_CASES],  # type: ignore[arg-type]
)
async def test_execution_correctness(case: dict[str, Any], require_real_api_key: None) -> None:
    """Test execution correctness evaluation with real LLM calls.

    Validates that the executor correctly reports success/failure and provides
    quality output when executing tasks.
    """
    # Extract test case data
    task_description = case["task_description"]
    expected_result = case["execution_result"]

    # Execute the task with empty tool list (simulates no tools available)
    result = await execute_task(task_description)

    # Build evaluation prompt from execution result
    eval_prompt = f"""Task: {task_description}

Execution Result:
- Success: {result.success if result else False}
- Output: {result.output if result else "Execution failed"}

Expected Quality: {expected_result}

Assess the execution correctness and output quality."""

    # Evaluate execution correctness with LLM judge
    score = await evaluate(EvalDimension.EXECUTION_CORRECTNESS, eval_prompt)

    # Check score meets pass threshold
    if not score.passed:
        msg = f"Execution correctness score {score.score}/5: {score.reasoning}"
        raise AssertionError(msg)
