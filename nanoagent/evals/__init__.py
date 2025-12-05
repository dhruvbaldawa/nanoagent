# ABOUTME: Eval framework initialization
# ABOUTME: Exports models and evaluator for quality assessment

from nanoagent.evals.judge import evaluate, evaluator
from nanoagent.evals.models import EvalDimension, EvalScore

__all__ = ["EvalDimension", "EvalScore", "evaluate", "evaluator"]
