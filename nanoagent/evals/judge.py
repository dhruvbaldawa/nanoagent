# ABOUTME: LLM-as-judge evaluator agent for structured evaluation
# ABOUTME: Scores agent outputs on quality dimensions using Pydantic AI

import logging

import httpx
from pydantic_ai import Agent, ModelHTTPError, UnexpectedModelBehavior

from nanoagent.config import get_settings
from nanoagent.evals.models import EvalDimension, EvalScore

logger = logging.getLogger(__name__)

# System prompt for LLM-as-judge evaluation
BASE_SYSTEM_PROMPT = """You are an expert evaluator. Your job is to score outputs on a 1-5 scale.

Scoring rubric:
1 = Poor: Major gaps, incorrect, or incomplete
2 = Fair: Works but has significant issues
3 = Good: Meets requirements, acceptable quality
4 = Very Good: Exceeds requirements in some ways
5 = Excellent: Outstanding quality, minimal issues

Evaluate fairly and provide clear reasoning for your score."""

# Dimension-specific evaluation prompts
DIMENSION_PROMPTS = {
    EvalDimension.PLAN_QUALITY: """Evaluate the quality of a task plan. Consider:
- Clear decomposition of the goal into concrete steps
- Realistic ordering of tasks
- Completeness of coverage
- Feasibility of the plan""",
    EvalDimension.REFLECTION_ACCURACY: """Evaluate the accuracy and quality of reflection. Consider:
- Correct identification of gaps
- Realistic assessment of progress
- Actionable next steps
- Avoiding false positives/negatives""",
    EvalDimension.EXECUTION_CORRECTNESS: """Evaluate the correctness of task execution. Consider:
- Tasks completed as described
- Results match expectations
- Error handling appropriateness
- Output quality and accuracy""",
    EvalDimension.CONVERGENCE_BEHAVIOR: """Evaluate how well the agent converges toward the goal. Consider:
- Progress toward objective
- Reduction in identified gaps
- Quality improvement over iterations
- Efficiency of the approach""",
}


# Initialize evaluator agent with Pydantic AI
# Agent[None, EvalScore] means: no dependencies, returns EvalScore
# type: ignore[assignment] - Pydantic AI's generic type system doesn't properly propagate
# at initialization time, but the agent is correctly configured at runtime
evaluator: Agent[None, EvalScore] = Agent(  # type: ignore[assignment]
    model=get_settings().get_model_instance(get_settings().reflector_model),
    output_type=EvalScore,
    system_prompt=BASE_SYSTEM_PROMPT,
)


async def evaluate(dimension: EvalDimension, prompt: str, pass_threshold: int = 3) -> EvalScore:
    """
    Evaluate content on a specific quality dimension.

    Args:
        dimension: The quality dimension to evaluate
        prompt: The evaluation prompt/content to judge
        pass_threshold: Minimum score to pass (default 3, range 1-5)

    Returns:
        EvalScore with dimension, score, reasoning, and pass_threshold

    Raises:
        ValueError: If dimension is invalid, prompt is empty, or threshold out of range
        RuntimeError: If LLM API call fails
    """
    # Input validation
    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty or whitespace-only")

    if not 1 <= pass_threshold <= 5:
        raise ValueError(f"pass_threshold must be between 1-5, got {pass_threshold}")

    # Validate dimension is known
    if dimension not in DIMENSION_PROMPTS:
        raise ValueError(f"Invalid dimension: {dimension}. Must be one of: {', '.join(d.value for d in EvalDimension)}")

    # Get dimension-specific evaluation criteria
    dimension_prompt = DIMENSION_PROMPTS[dimension]

    # Build full evaluation prompt
    full_prompt = f"""{dimension_prompt}

Content to evaluate:
{prompt}

Provide your evaluation as a structured score."""

    try:
        # Run evaluator and return result with dimension and threshold set
        result = await evaluator.run(full_prompt)  # type: ignore[arg-type]
        output = result.output

        # Ensure dimension and threshold match request
        output.dimension = dimension
        output.pass_threshold = pass_threshold

        logger.info(
            "Evaluation completed",
            extra={
                "dimension": dimension.value,
                "score": output.score,
                "passed": output.score >= pass_threshold,
            },
        )
        return output

    except ModelHTTPError as e:
        logger.error(
            "LLM API error during evaluation",
            extra={
                "dimension": dimension.value,
                "error_type": "api_error",
                "status_code": e.status_code,
                "prompt_length": len(prompt),
            },
            exc_info=True,
        )
        raise RuntimeError(f"Evaluation failed due to LLM API error (status {e.status_code})") from e

    except UnexpectedModelBehavior as e:
        logger.error(
            "LLM produced invalid output during evaluation",
            extra={
                "dimension": dimension.value,
                "error_type": "model_behavior",
                "error_message": str(e),
            },
            exc_info=True,
        )
        raise ValueError(f"Evaluation failed: LLM output did not match EvalScore schema. {str(e)}") from e

    except (httpx.TimeoutException, httpx.ConnectError) as e:
        logger.error(
            "Network error during evaluation",
            extra={
                "dimension": dimension.value,
                "error_type": "network_error",
                "exception_type": type(e).__name__,
            },
            exc_info=True,
        )
        raise RuntimeError(f"Evaluation failed due to network error: {type(e).__name__}") from e

    except Exception as e:
        logger.error(
            "Unexpected error during evaluation",
            extra={
                "dimension": dimension.value,
                "error_type": "unexpected",
                "exception_type": type(e).__name__,
            },
            exc_info=True,
        )
        raise
