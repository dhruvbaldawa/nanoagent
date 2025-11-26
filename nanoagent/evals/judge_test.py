# ABOUTME: Tests for LLM-as-judge evaluator
# ABOUTME: Validates judge agent produces structured EvalScore outputs

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from pydantic_ai import ModelHTTPError, UnexpectedModelBehavior
from pydantic_ai.models.test import TestModel

from nanoagent.evals.judge import evaluate, evaluator
from nanoagent.evals.models import EvalDimension, EvalScore


class TestEvaluate:
    @pytest.mark.asyncio
    async def test_returns_eval_score(self) -> None:
        """Test that evaluate returns an EvalScore instance."""
        with evaluator.override(model=TestModel()):
            score = await evaluator.run("Test prompt")
            assert isinstance(score.output, EvalScore)

    @pytest.mark.asyncio
    async def test_sets_dimension_correctly(self) -> None:
        """Test that dimension is set correctly in the output."""
        with evaluator.override(model=TestModel()):
            score = await evaluator.run("Test prompt for PLAN_QUALITY")
            assert isinstance(score.output, EvalScore)
            assert score.output.dimension in EvalDimension

    @pytest.mark.asyncio
    async def test_score_within_valid_range(self) -> None:
        """Test that returned score is between 1-5."""
        with evaluator.override(model=TestModel()):
            score = await evaluator.run("Test prompt")
            assert isinstance(score.output, EvalScore)
            assert 1 <= score.output.score <= 5

    @pytest.mark.asyncio
    async def test_reasoning_present_and_valid(self) -> None:
        """Test that reasoning is present and meets minimum length."""
        with evaluator.override(model=TestModel()):
            score = await evaluator.run("Test prompt")
            assert isinstance(score.output, EvalScore)
            assert len(score.output.reasoning) >= 10

    @pytest.mark.asyncio
    async def test_pass_threshold_default(self) -> None:
        """Test that pass_threshold defaults to 3."""
        with evaluator.override(model=TestModel()):
            score = await evaluator.run("Test prompt")
            assert isinstance(score.output, EvalScore)
            assert score.output.pass_threshold == 3

    @pytest.mark.asyncio
    async def test_all_dimensions_evaluable(self) -> None:
        """Test that evaluator can handle all dimensions."""
        with evaluator.override(model=TestModel()):
            for dimension in EvalDimension:
                prompt = f"Evaluate {dimension.value}"
                score = await evaluator.run(prompt)
                assert isinstance(score.output, EvalScore)
                # TestModel returns a valid but predictable EvalScore
                assert score.output.score >= 1 and score.output.score <= 5


class TestEvaluateFunction:
    """Test suite for the evaluate() function wrapper."""

    @pytest.mark.asyncio
    async def test_evaluate_returns_eval_score_with_dimension(self) -> None:
        """Test that evaluate() returns EvalScore with correct dimension."""
        from nanoagent.evals.judge import evaluate

        with evaluator.override(model=TestModel()):
            score = await evaluate(EvalDimension.PLAN_QUALITY, "Test prompt")
            assert isinstance(score, EvalScore)
            assert score.dimension == EvalDimension.PLAN_QUALITY

    @pytest.mark.asyncio
    async def test_evaluate_respects_custom_pass_threshold(self) -> None:
        """Test that evaluate() respects custom pass_threshold parameter."""
        from nanoagent.evals.judge import evaluate

        with evaluator.override(model=TestModel()):
            score = await evaluate(EvalDimension.REFLECTION_ACCURACY, "Test prompt", pass_threshold=5)
            assert score.pass_threshold == 5

    @pytest.mark.asyncio
    async def test_evaluate_with_all_dimensions(self) -> None:
        """Test that evaluate() works with all dimensions."""
        from nanoagent.evals.judge import evaluate

        with evaluator.override(model=TestModel()):
            for dimension in EvalDimension:
                score = await evaluate(dimension, f"Evaluate {dimension.value}")
                assert isinstance(score, EvalScore)
                assert score.dimension == dimension

    @pytest.mark.asyncio
    async def test_evaluate_empty_prompt_raises_error(self) -> None:
        """Test that evaluate() raises ValueError for empty prompt."""
        from nanoagent.evals.judge import evaluate

        with evaluator.override(model=TestModel()):
            with pytest.raises(ValueError, match="Prompt cannot be empty"):
                await evaluate(EvalDimension.PLAN_QUALITY, "")

    @pytest.mark.asyncio
    async def test_evaluate_whitespace_only_prompt_raises_error(self) -> None:
        """Test that evaluate() raises ValueError for whitespace-only prompt."""
        from nanoagent.evals.judge import evaluate

        with evaluator.override(model=TestModel()):
            with pytest.raises(ValueError, match="Prompt cannot be empty"):
                await evaluate(EvalDimension.PLAN_QUALITY, "   ")

    @pytest.mark.asyncio
    async def test_evaluate_invalid_threshold_below_min_raises_error(self) -> None:
        """Test that evaluate() raises ValueError for threshold < 1."""
        from nanoagent.evals.judge import evaluate

        with evaluator.override(model=TestModel()):
            with pytest.raises(ValueError, match="pass_threshold must be between 1-5"):
                await evaluate(EvalDimension.PLAN_QUALITY, "Test", pass_threshold=0)

    @pytest.mark.asyncio
    async def test_evaluate_invalid_threshold_above_max_raises_error(self) -> None:
        """Test that evaluate() raises ValueError for threshold > 5."""
        from nanoagent.evals.judge import evaluate

        with evaluator.override(model=TestModel()):
            with pytest.raises(ValueError, match="pass_threshold must be between 1-5"):
                await evaluate(EvalDimension.PLAN_QUALITY, "Test", pass_threshold=6)

    @pytest.mark.asyncio
    async def test_evaluate_invalid_dimension_raises_error(self) -> None:
        """Test that evaluate() raises ValueError for invalid dimension."""
        from nanoagent.evals.judge import evaluate

        with evaluator.override(model=TestModel()):
            # Pass an invalid dimension-like object (not in enum)
            with pytest.raises(ValueError, match="Invalid dimension"):
                await evaluate("invalid_dimension", "Test prompt")  # type: ignore[arg-type]


class TestErrorHandling:
    """Test suite for error handling in evaluate() function."""

    @pytest.mark.asyncio
    async def test_evaluate_api_error_raises_runtime_error(self) -> None:
        """Test that ModelHTTPError is caught and re-raised as RuntimeError."""
        from nanoagent.evals.judge import evaluator as judge_evaluator

        with patch.object(judge_evaluator, "run", new_callable=AsyncMock) as mock_run:
            mock_run.side_effect = ModelHTTPError(status_code=500, model_name="anthropic")
            with pytest.raises(RuntimeError, match="API error.*500"):
                with judge_evaluator.override(model=TestModel()):
                    await evaluate(EvalDimension.PLAN_QUALITY, "Test prompt")

    @pytest.mark.asyncio
    async def test_evaluate_timeout_error_raises_runtime_error(self) -> None:
        """Test that network timeout is caught and re-raised as RuntimeError."""
        from nanoagent.evals.judge import evaluator as judge_evaluator

        with patch.object(judge_evaluator, "run", new_callable=AsyncMock) as mock_run:
            mock_run.side_effect = httpx.TimeoutException("Request timeout")
            with pytest.raises(RuntimeError, match="network error.*Timeout"):
                with judge_evaluator.override(model=TestModel()):
                    await evaluate(EvalDimension.PLAN_QUALITY, "Test prompt")

    @pytest.mark.asyncio
    async def test_evaluate_connect_error_raises_runtime_error(self) -> None:
        """Test that network connection error is caught and re-raised as RuntimeError."""
        from nanoagent.evals.judge import evaluator as judge_evaluator

        with patch.object(judge_evaluator, "run", new_callable=AsyncMock) as mock_run:
            mock_run.side_effect = httpx.ConnectError("Connection failed")
            with pytest.raises(RuntimeError, match="network error.*Connect"):
                with judge_evaluator.override(model=TestModel()):
                    await evaluate(EvalDimension.PLAN_QUALITY, "Test prompt")

    @pytest.mark.asyncio
    async def test_evaluate_unexpected_behavior_raises_value_error(self) -> None:
        """Test that UnexpectedModelBehavior is caught and re-raised as ValueError."""
        from nanoagent.evals.judge import evaluator as judge_evaluator

        with patch.object(judge_evaluator, "run", new_callable=AsyncMock) as mock_run:
            mock_run.side_effect = UnexpectedModelBehavior("Output did not match schema")
            with pytest.raises(ValueError, match="did not match EvalScore schema"):
                with judge_evaluator.override(model=TestModel()):
                    await evaluate(EvalDimension.PLAN_QUALITY, "Test prompt")
