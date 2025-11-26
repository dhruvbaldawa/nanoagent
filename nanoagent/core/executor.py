# ABOUTME: Executor agent that uses tools to complete tasks
# ABOUTME: Returns structured ExecutionResult with success status and output

import logging

import httpx
from pydantic import BaseModel, Field
from pydantic_ai import Agent, ModelHTTPError, UnexpectedModelBehavior

from nanoagent.config import get_settings
from nanoagent.models.schemas import ExecutionResult

logger = logging.getLogger(__name__)


class ExecutorDeps(BaseModel):
    """Dependencies injected into executor agent"""

    task: str = Field(..., description="Task description to execute")
    available_tools: dict[str, str] = Field(default_factory=dict, description="Mapping of tool names to descriptions")


# System prompt for task execution
SYSTEM_PROMPT = """You are an executor agent. You receive a task and a set of available tools.

Your job is to:
1. Analyze the task carefully
2. Use the available tools to complete it
3. Return detailed output explaining what you did
4. Report success=true if the task was completed successfully, false if it failed

When tools are available:
- Call them with appropriate parameters
- Combine tool results to complete the task
- If you cannot complete the task with available tools, return success=false with explanation

Provide thorough output that explains your reasoning and what you accomplished."""

# Initialize executor agent with Pydantic AI
# Agent[ExecutorDeps, ExecutionResult] means: takes ExecutorDeps, returns ExecutionResult
# Model is configured via settings (EXECUTOR_MODEL env var)
# type: ignore[assignment] - Pydantic AI's generic type system doesn't properly propagate
# at initialization time, but the agent is correctly configured at runtime
executor: Agent[ExecutorDeps, ExecutionResult] = Agent(  # type: ignore[assignment]
    model=get_settings().get_model_instance(get_settings().executor_model),
    output_type=ExecutionResult,
    deps_type=ExecutorDeps,
    system_prompt=SYSTEM_PROMPT,
)


async def execute_task(task: str, available_tools: dict[str, str] | None = None) -> ExecutionResult:
    """
    Execute a task using the executor agent.

    Args:
        task: Task description to execute
        available_tools: Optional mapping of tool names to descriptions

    Returns:
        ExecutionResult with success status and output

    Raises:
        ValueError: If task is empty/whitespace-only or LLM produces invalid output
        RuntimeError: If API call fails (HTTP error) or network error occurs
    """
    # Input validation
    if not task or not task.strip():
        raise ValueError("Task cannot be empty or whitespace-only")

    if len(task) > 2000:
        logger.warning("Task exceeds recommended length", extra={"task_length": len(task), "limit": 2000})

    try:
        # Create dependencies for this execution
        deps = ExecutorDeps(
            task=task,
            available_tools=available_tools or {},
        )

        result = await executor.run(task, deps=deps)  # type: ignore[arg-type]
        output = result.output

        logger.info(
            "Task execution succeeded",
            extra={
                "task": task[:100],
                "success": output.success,
                "output_length": len(output.output),
            },
        )
        return output

    except ModelHTTPError as e:
        logger.error(
            "LLM API error during task execution",
            extra={
                "task": task[:100],
                "error_type": "api_error",
                "status_code": e.status_code,
            },
            exc_info=True,
        )
        raise RuntimeError(f"Task execution failed due to LLM API error (status {e.status_code})") from e

    except UnexpectedModelBehavior as e:
        logger.error(
            "LLM produced invalid output during task execution",
            extra={
                "task": task[:100],
                "error_type": "model_behavior",
                "error_message": str(e),
            },
            exc_info=True,
        )
        # Re-raise so caller knows structured output validation failed
        raise ValueError(f"Task execution failed: LLM output did not match ExecutionResult schema. {str(e)}") from e

    except (httpx.TimeoutException, httpx.ConnectError) as e:
        logger.error(
            "Network error during task execution",
            extra={
                "task": task[:100],
                "error_type": "network_error",
                "exception_type": type(e).__name__,
            },
            exc_info=True,
        )
        raise RuntimeError(f"Task execution failed due to network error: {type(e).__name__}") from e

    except Exception as e:
        logger.error(
            "Unexpected error during task execution",
            extra={
                "task": task[:100],
                "error_type": "unexpected",
                "exception_type": type(e).__name__,
            },
            exc_info=True,
        )
        raise
