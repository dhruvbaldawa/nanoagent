# ABOUTME: Tests for eval framework data models
# ABOUTME: Validates EvalDimension enum and EvalScore structured output

import pytest
from pydantic import ValidationError

from nanoagent.evals.models import EvalDimension, EvalScore


class TestEvalDimension:
    def test_has_four_dimensions(self) -> None:
        """Verify all 4 quality dimensions are defined."""
        assert len(EvalDimension) == 4
        assert EvalDimension.PLAN_QUALITY.value == "plan_quality"
        assert EvalDimension.REFLECTION_ACCURACY.value == "reflection_accuracy"
        assert EvalDimension.EXECUTION_CORRECTNESS.value == "execution_correctness"
        assert EvalDimension.CONVERGENCE_BEHAVIOR.value == "convergence_behavior"


class TestEvalScore:
    def test_passed_when_score_meets_threshold(self) -> None:
        """Test passed property returns True when score >= threshold."""
        score = EvalScore(
            dimension=EvalDimension.PLAN_QUALITY,
            score=3,
            reasoning="Task decomposition is acceptable",
        )
        assert score.passed is True

    def test_passed_when_score_exceeds_threshold(self) -> None:
        """Test passed property returns True when score > threshold."""
        score = EvalScore(
            dimension=EvalDimension.PLAN_QUALITY,
            score=5,
            reasoning="Excellent task decomposition",
        )
        assert score.passed is True

    def test_failed_when_score_below_threshold(self) -> None:
        """Test passed property returns False when score < threshold."""
        score = EvalScore(
            dimension=EvalDimension.PLAN_QUALITY,
            score=2,
            reasoning="Tasks are too vague and unclear",
        )
        assert score.passed is False

    def test_invalid_score_too_high_raises_validation_error(self) -> None:
        """Test that score > 5 raises ValidationError."""
        with pytest.raises(ValidationError):
            EvalScore(
                dimension=EvalDimension.PLAN_QUALITY,
                score=6,
                reasoning="Invalid score",
            )

    def test_invalid_score_too_low_raises_validation_error(self) -> None:
        """Test that score < 1 raises ValidationError."""
        with pytest.raises(ValidationError):
            EvalScore(
                dimension=EvalDimension.PLAN_QUALITY,
                score=0,
                reasoning="Invalid score",
            )

    def test_custom_pass_threshold(self) -> None:
        """Test that custom pass_threshold is respected."""
        score = EvalScore(
            dimension=EvalDimension.REFLECTION_ACCURACY,
            score=4,
            reasoning="Good reflection accuracy",
            pass_threshold=5,
        )
        assert score.passed is False

    def test_reasoning_too_short_raises_validation_error(self) -> None:
        """Test that reasoning shorter than 10 chars raises ValidationError."""
        with pytest.raises(ValidationError):
            EvalScore(
                dimension=EvalDimension.EXECUTION_CORRECTNESS,
                score=3,
                reasoning="Bad",
            )

    def test_all_dimensions_work(self) -> None:
        """Test that all dimensions can be used in EvalScore."""
        for dimension in EvalDimension:
            score = EvalScore(
                dimension=dimension,
                score=3,
                reasoning="This is a valid test evaluation",
            )
            assert score.dimension == dimension
            assert score.passed is True
