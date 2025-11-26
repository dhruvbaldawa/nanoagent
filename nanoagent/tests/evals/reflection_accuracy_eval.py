# ABOUTME: Eval tests for reflection accuracy dimension
# ABOUTME: Validates reflector gap detection and done flag accuracy

from typing import Any

import pytest

from nanoagent.core.reflector import reflect_on_progress
from nanoagent.evals.judge import evaluate
from nanoagent.evals.models import EvalDimension
from nanoagent.models.schemas import Task, TaskStatus
from nanoagent.tests.evals.cases import REFLECTION_ACCURACY_CASES


@pytest.mark.eval
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "case",
    REFLECTION_ACCURACY_CASES,
    ids=[c["name"] for c in REFLECTION_ACCURACY_CASES],  # type: ignore[arg-type]
)
async def test_reflection_accuracy(case: dict[str, Any], require_real_api_key: None) -> None:
    """Test reflection accuracy evaluation with real LLM calls.

    Validates that the reflector correctly identifies gaps, detects completion,
    and provides accurate progress assessment.
    """
    # Parse case data to determine goal and task states
    execution_summary = case["execution_summary"]

    # For completed case: all tasks done
    if "All" in execution_summary and "completed" in execution_summary:
        goal = "Complete development project"
        completed_tasks = [
            Task(id="task0001", description="Analyzed requirements", status=TaskStatus.DONE),
            Task(id="task0002", description="Designed architecture", status=TaskStatus.DONE),
            Task(id="task0003", description="Implemented core features", status=TaskStatus.DONE),
            Task(id="task0004", description="Tested functionality", status=TaskStatus.DONE),
            Task(id="task0005", description="Deployed to production", status=TaskStatus.DONE),
        ]
        pending_tasks: list[Task] = []
    # For incomplete case: some tasks done, some pending
    else:
        goal = "Complete development project with testing and deployment"
        completed_tasks = [
            Task(id="task0001", description="Analyzed requirements", status=TaskStatus.DONE),
            Task(id="task0002", description="Designed architecture", status=TaskStatus.DONE),
            Task(id="task0003", description="Implemented core features", status=TaskStatus.DONE),
        ]
        pending_tasks = [
            Task(id="task0004", description="Database migration", status=TaskStatus.PENDING),
            Task(id="task0005", description="Test coverage and deployment", status=TaskStatus.PENDING),
        ]

    # Call reflector to assess progress
    reflection = await reflect_on_progress(goal, completed_tasks, pending_tasks)

    # Build evaluation prompt from reflection output
    gaps_str = "\n".join([f"- {gap}" for gap in reflection.gaps]) if reflection.gaps else "No gaps identified"
    new_tasks_str = (
        "\n".join([f"- {task}" for task in reflection.new_tasks]) if reflection.new_tasks else "No new tasks identified"
    )

    eval_prompt = f"""Goal: {goal}

Completed Tasks: {len(completed_tasks)}
Pending Tasks: {len(pending_tasks)}

Reflector Assessment:
- Done: {reflection.done}

Identified Gaps:
{gaps_str}

Suggested New Tasks:
{new_tasks_str}

Execution Summary:
{execution_summary}"""

    # Evaluate reflection accuracy with LLM judge
    score = await evaluate(EvalDimension.REFLECTION_ACCURACY, eval_prompt)

    # Check score meets pass threshold
    if not score.passed:
        msg = f"Reflection accuracy score {score.score}/5: {score.reasoning}"
        raise AssertionError(msg)
