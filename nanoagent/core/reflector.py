# ABOUTME: Reflector agent that evaluates progress and identifies gaps
# ABOUTME: Returns structured ReflectionOutput with done status, gaps, and new tasks

import logging

import httpx
from pydantic_ai import Agent, ModelHTTPError, UnexpectedModelBehavior

from nanoagent.models.schemas import ReflectionOutput, Task

logger = logging.getLogger(__name__)


# System prompt for reflection analysis
SYSTEM_PROMPT = """You are a reflection agent. Your job is to analyze progress toward a goal and identify gaps.

Given a goal and task history (completed and pending tasks), answer these four questions:

1. **Is the goal fully accomplished?** (done flag)
   - True only if all critical aspects of the goal are complete
   - False if significant work remains

2. **What critical information is missing?** (gaps list)
   - List specific missing capabilities, information, or deliverables
   - Focus on what's needed to complete the goal
   - Be thorough but concise (3-5 gaps max)

3. **What new tasks would fill those gaps?** (new_tasks list)
   - Suggest actionable next steps to address identified gaps
   - Each task should be concrete and implementable
   - Don't duplicate pending tasks that already address these gaps
   - Limit to 3-5 new tasks max

4. **Which pending tasks are now irrelevant?** (complete_ids list)
   - List IDs of tasks that no longer serve the goal
   - Leave empty if all pending tasks remain relevant
   - Only include task IDs, not descriptions

Be thorough in your analysis but concise in your output. Focus on what's missing, not what's been done."""

# Initialize reflector agent with Pydantic AI
# Agent[None, ReflectionOutput] means: no dependencies, returns ReflectionOutput
# type: ignore[assignment] - Pydantic AI's generic type system doesn't properly propagate
# at initialization time, but the agent is correctly configured at runtime
reflector: Agent[None, ReflectionOutput] = Agent(  # type: ignore[assignment]
    model="anthropic:claude-sonnet-4-5-20250514",
    output_type=ReflectionOutput,
    system_prompt=SYSTEM_PROMPT,
)


async def reflect_on_progress(goal: str, completed_tasks: list[Task], pending_tasks: list[Task]) -> ReflectionOutput:
    """
    Reflect on progress toward a goal and identify gaps.

    Args:
        goal: The goal being pursued
        completed_tasks: List of tasks that have been completed
        pending_tasks: List of tasks that are pending

    Returns:
        ReflectionOutput with done status, gaps, new_tasks, and complete_ids

    Raises:
        ValueError: If goal is empty/whitespace-only, task lists invalid, or LLM produces invalid output
        TypeError: If task list contains invalid task objects
        RuntimeError: If API call fails (HTTP error) or network error occurs
    """
    # Input validation
    if not goal or not goal.strip():
        raise ValueError("Goal cannot be empty or whitespace-only")

    # Validate task lists - defensive validation for runtime safety
    if not isinstance(completed_tasks, list):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise TypeError(f"completed_tasks must be a list, got {type(completed_tasks).__name__}")
    if not isinstance(pending_tasks, list):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise TypeError(f"pending_tasks must be a list, got {type(pending_tasks).__name__}")

    # Validate individual tasks
    all_tasks = completed_tasks + pending_tasks
    for i, task in enumerate(all_tasks):
        if task is None:  # pyright: ignore[reportUnnecessaryComparison]
            raise ValueError(f"Task at index {i} is None")

    # Check for duplicate task IDs
    task_ids = [task.id for task in all_tasks]
    if len(task_ids) != len(set(task_ids)):
        duplicates = [tid for tid in set(task_ids) if task_ids.count(tid) > 1]
        raise ValueError(f"Duplicate task IDs found: {duplicates}")

    if len(goal) > 2000:
        logger.warning("Goal exceeds recommended length", extra={"goal_length": len(goal), "limit": 2000})

    try:
        # Build context string from task history
        completed_context = ""
        if completed_tasks:
            completed_context = "Completed tasks:\n"
            for task in completed_tasks:
                completed_context += f"- {task.description}"
                if task.result:
                    completed_context += f" (Result: {task.result})"
                completed_context += "\n"

        pending_context = ""
        if pending_tasks:
            pending_context = "Pending tasks:\n"
            for task in pending_tasks:
                pending_context += f"- [{task.id}] {task.description}\n"

        # Combine into full prompt
        full_prompt = f"""Goal: {goal}

{completed_context}

{pending_context}

Analyze this progress and provide your reflection in the structured format."""

        result = await reflector.run(full_prompt)  # type: ignore[arg-type]
        output = result.output

        logger.info(
            "Reflection completed",
            extra={
                "goal": goal[:100],
                "completed_count": len(completed_tasks),
                "pending_count": len(pending_tasks),
                "done": output.done,
                "gaps_count": len(output.gaps),
                "new_tasks_count": len(output.new_tasks),
            },
        )
        return output

    except ModelHTTPError as e:
        logger.error(
            "LLM API error during reflection",
            extra={
                "goal": goal[:100],
                "error_type": "api_error",
                "status_code": e.status_code,
            },
            exc_info=True,
        )
        raise RuntimeError(f"Reflection failed due to LLM API error (status {e.status_code})") from e

    except UnexpectedModelBehavior as e:
        logger.error(
            "LLM produced invalid output during reflection",
            extra={
                "goal": goal[:100],
                "error_type": "model_behavior",
                "error_message": str(e),
            },
            exc_info=True,
        )
        # Re-raise so caller knows structured output validation failed
        raise ValueError(f"Reflection failed: LLM output did not match ReflectionOutput schema. {str(e)}") from e

    except (httpx.TimeoutException, httpx.ConnectError) as e:
        logger.error(
            "Network error during reflection",
            extra={
                "goal": goal[:100],
                "error_type": "network_error",
                "exception_type": type(e).__name__,
            },
            exc_info=True,
        )
        raise RuntimeError(f"Reflection failed due to network error: {type(e).__name__}") from e

    except Exception as e:
        logger.error(
            "Unexpected error during reflection",
            extra={
                "goal": goal[:100],
                "error_type": "unexpected",
                "exception_type": type(e).__name__,
            },
            exc_info=True,
        )
        raise
