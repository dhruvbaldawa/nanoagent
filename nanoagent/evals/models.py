# ABOUTME: Pydantic models for eval framework
# ABOUTME: Structured outputs for LLM-as-judge evaluations

from enum import Enum

from pydantic import BaseModel, Field


class EvalDimension(str, Enum):
    """Quality dimensions for agent evaluation."""

    PLAN_QUALITY = "plan_quality"
    REFLECTION_ACCURACY = "reflection_accuracy"
    EXECUTION_CORRECTNESS = "execution_correctness"
    CONVERGENCE_BEHAVIOR = "convergence_behavior"


class EvalScore(BaseModel):
    """Structured evaluation score with reasoning."""

    dimension: EvalDimension = Field(..., description="Quality dimension being evaluated")
    score: int = Field(
        ...,
        ge=1,
        le=5,
        description="Score from 1 (poor) to 5 (excellent)",
    )
    reasoning: str = Field(
        ...,
        min_length=10,
        description="Explanation for the score",
    )
    pass_threshold: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Minimum score to pass (default 3)",
    )

    @property
    def passed(self) -> bool:
        """Whether this evaluation passed the threshold."""
        return self.score >= self.pass_threshold
