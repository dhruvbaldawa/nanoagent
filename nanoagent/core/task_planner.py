# ABOUTME: TaskPlanner agent that decomposes goals into actionable tasks
# ABOUTME: Uses Pydantic AI structured outputs to validate critical risk #1

import logging

import httpx
from pydantic_ai import Agent, ModelHTTPError, UnexpectedModelBehavior

from nanoagent.config import get_settings
from nanoagent.models.schemas import TaskPlanOutput

logger = logging.getLogger(__name__)

# System prompt for task decomposition
SYSTEM_PROMPT = """You are an expert task decomposition agent. Your role is to break down high-level goals
into specific, actionable tasks.

For clear, well-defined goals:
- Return 3-7 specific tasks that directly contribute to achieving the goal
- Make tasks concrete and measurable
- Order tasks in a logical dependency sequence
- Avoid vague or overlapping tasks
- Each task should be completable independently or in sequence

For ambiguous or unclear goals:
- Ask 2-3 clarifying questions to better understand requirements
- You can still provide some initial tasks if you have reasonable assumptions
- Questions should help narrow down scope, technology choices, or requirements

Always return structured output with your task list and any questions."""

# Initialize task planner agent with Pydantic AI
# Agent[None, TaskPlanOutput] means: no dependencies (None), output type TaskPlanOutput
# Model is configured via settings (TASK_PLANNER_MODEL env var)
# type: ignore[assignment] - Pydantic AI's generic type system doesn't properly propagate
# at initialization time, but the agent is correctly configured at runtime
task_planner: Agent[None, TaskPlanOutput] = Agent(  # type: ignore[assignment]
    model=get_settings().get_model_instance(get_settings().task_planner_model),
    output_type=TaskPlanOutput,
    system_prompt=SYSTEM_PROMPT,
)


async def plan_tasks(goal: str) -> TaskPlanOutput | None:
    """
    Decompose a goal into actionable tasks using the task planner agent.

    Args:
        goal: High-level goal description to decompose into tasks

    Returns:
        TaskPlanOutput with tasks and optional clarifying questions, or None if planning fails

    Raises:
        ValueError: If goal is empty or whitespace-only
    """
    # Input validation
    if not goal or not goal.strip():
        raise ValueError("Goal cannot be empty or whitespace-only")

    if len(goal) > 1000:
        logger.warning("Goal exceeds recommended length", extra={"goal_length": len(goal), "limit": 1000})

    try:
        result = await task_planner.run(goal)  # type: ignore[arg-type]
        output = result.output

        logger.info(
            "Task planning succeeded",
            extra={
                "goal": goal[:100],
                "task_count": len(output.tasks),
                "question_count": len(output.questions),
            },
        )
        return output

    except ModelHTTPError as e:
        logger.error(
            "LLM API error during task planning",
            extra={
                "goal": goal[:100],
                "error_type": "api_error",
                "status_code": e.status_code,
            },
            exc_info=True,
        )
        return None

    except UnexpectedModelBehavior as e:
        logger.error(
            "LLM produced invalid output during task planning",
            extra={
                "goal": goal[:100],
                "error_type": "model_behavior",
                "error_message": str(e),
            },
            exc_info=True,
        )
        # Re-raise so caller knows structured output validation failed (Critical Risk #1)
        raise ValueError(f"Task planning failed: LLM output did not match TaskPlanOutput schema. {str(e)}") from e

    except (httpx.TimeoutException, httpx.ConnectError) as e:
        logger.error(
            "Network error during task planning",
            extra={
                "goal": goal[:100],
                "error_type": "network_error",
                "exception_type": type(e).__name__,
            },
            exc_info=True,
        )
        return None

    except Exception as e:
        logger.error(
            "Unexpected error during task planning",
            extra={
                "goal": goal[:100],
                "error_type": "unexpected",
                "exception_type": type(e).__name__,
            },
            exc_info=True,
        )
        raise
