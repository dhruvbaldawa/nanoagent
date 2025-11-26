# Eval Framework Feature Plan

## Overview
Two-tier testing strategy: fast unit tests (Tier 1) + quality evaluation for prompt/model iteration (Tier 2).

**Problem**: Current tests using `ALLOW_MODEL_REQUESTS=true` are slow (5+ min) and flaky. Additionally, there's no systematic way to iterate on prompts/models and measure quality improvements.

**Solution**:
- **Tier 1 (COMPLETE)**: Pydantic AI's built-in `TestModel` + `Agent.override()` for fast, deterministic unit tests
- **Tier 2 (NOW)**: Custom lightweight LLM-as-judge for quality evaluation (~70 LOC, no new dependencies)

---

## Success Criteria

### Tier 1 (COMPLETE)
- [x] All 202 tests converted to use TestModel + Agent.override()
- [x] `pytest nanoagent/` runs in 0.42s, 100% passing
- [x] No new dependencies added
- [x] Total LOC change: ~50 LOC

### Tier 2 (NOW)
- [ ] Custom LLM-as-judge evaluator (~40 LOC)
- [ ] EvalScore/EvalDimension schemas (~30 LOC)
- [ ] 10 eval cases across 4 quality dimensions
- [ ] Evals run with `pytest -m eval` (not in CI)
- [ ] No new dependencies (uses existing Pydantic AI)
- [ ] >80% of evals score ≥3/5

---

## Research Findings

### Key Finding: Separate Concerns for Unit Tests vs Quality Evaluation

Research from 3 exploration agents revealed that **unit testing** and **quality evaluation** are distinct concerns requiring different tools:

1. **Unit Testing** → Pydantic AI's built-in `TestModel` + `Agent.override()`
2. **Quality Evaluation** → DeepEval (or pydantic-evals)

### Tier 1: Unit Testing (TestModel)

**Key Findings:**
1. Pydantic AI already has `TestModel` and `Agent.override()` for fast unit tests
2. This pattern is **already in use** in `task_planner_test.py` (lines 163-178)
3. No new dependencies required
4. LOC overhead: ~50 LOC total

**Pattern:**
```python
from pydantic_ai.models.test import TestModel

async def test_executor_calls_tool(self):
    with executor.override(model=TestModel()):
        result = await execute_task("test task")
        assert isinstance(result, ExecutionResult)
```

### Tier 2: Quality Evaluation (Framework Decision)

| Framework | Verdict | Reason |
|-----------|---------|--------|
| **Custom LLM-as-judge** | ✅ Chosen | ~70 LOC, no deps, fits LOC budget, full control |
| **DeepEval** | ❌ Too heavy | Adds dependencies, G-Eval overkill for 3 agents |
| **pydantic-evals** | ❌ Too new | Limited features, sparse documentation |
| **DSPy** | ❌ Overkill | Auto-optimization needs 50+ examples |
| **Ragas** | ❌ RAG-focused | Not agent-focused |

### Why Custom LLM-as-judge?

1. **LOC budget alignment** - Already exceeded 500 LOC target; DeepEval would add more
2. **No new dependencies** - Uses existing Pydantic AI Agent pattern
3. **Simple scoring** - 1-5 rubric sufficient for 4 quality dimensions
4. **Full control** - Can tune prompts and thresholds exactly as needed
5. **Fits existing patterns** - Same Agent + structured output pattern used throughout

---

## Architecture Decision

### Two-Tier Test Structure
```
nanoagent/
├── core/
│   ├── executor_test.py            # Tier 1: Unit tests (TestModel, fast, CI gate)
│   ├── reflector_test.py
│   ├── task_planner_test.py
│   └── ...
├── evals/                          # Eval framework (models, judge)
│   ├── __init__.py
│   ├── models.py                   # EvalScore, EvalDimension schemas (~30 LOC)
│   ├── models_test.py              # Unit tests (TestModel)
│   ├── judge.py                    # LLM-as-judge evaluator (~40 LOC)
│   └── judge_test.py               # Unit tests (TestModel)
└── tests/
    ├── integration/                # Existing integration tests
    │   ├── e2e_test.py
    │   └── orchestration_test.py
    └── evals/                      # Tier 2: Eval tests (real LLM, @pytest.mark.eval)
        ├── __init__.py
        ├── cases.py                # Test case definitions (data)
        ├── plan_quality_eval.py
        ├── reflection_accuracy_eval.py
        ├── execution_correctness_eval.py
        └── convergence_eval.py
```

**Run patterns**:
```bash
# Default: runs all tests EXCEPT eval (fast, CI-friendly)
pytest                               # 0.42s, 202+ tests, deterministic

# Run ONLY eval tests (manual, costs money)
pytest -m eval                       # Real LLM calls, ~2-5 min

# Run everything including evals
pytest -m ""                         # All tests
```

**pytest config** (pyproject.toml):
```toml
[tool.pytest.ini_options]
addopts = "-m 'not eval'"            # Skip eval by default
markers = ["eval: quality evaluations (real LLM calls, slow)"]
```

### Tier 1: Unit Testing (COMPLETE)

All 202 tests converted to use TestModel + Agent.override(). Fast, deterministic, no API calls.

### Tier 2: Quality Evaluation (LLM-as-judge)

**Quality Dimensions:**
1. **Plan quality** - Task decompositions logical, complete, actionable
2. **Reflection accuracy** - Identifies real gaps, knows when done
3. **Execution correctness** - Results accurately represent completion
4. **Convergence behavior** - Reaches goal in reasonable iterations

**Scoring Rubric:**
- 5: Excellent - Exceeds expectations, no issues
- 4: Good - Meets expectations with minor issues
- 3: Acceptable - Meets minimum bar, some issues (default pass threshold)
- 2: Poor - Below expectations, significant issues
- 1: Failed - Does not meet basic requirements

**Pattern:**
```python
from pydantic_ai import Agent
from nanoagent.evals.models import EvalScore, EvalDimension

evaluator = Agent(
    model=get_settings().reflector_model,
    output_type=EvalScore,
    system_prompt="You are an expert evaluator...",
)

async def evaluate(dimension: EvalDimension, prompt: str) -> EvalScore:
    result = await evaluator.run(prompt)
    return result.output

# In test
@pytest.mark.eval
async def test_plan_quality(case):
    plan = await plan_tasks(case["goal"])
    score = await evaluate(EvalDimension.PLAN_QUALITY, f"Goal: {case['goal']}\nPlan: {plan}")
    assert score.passed, f"Score {score.score}/5: {score.reasoning}"
```

---

## Risk Analysis

### Critical + Unknown
- **LLM-as-judge variability**: Same input may get different scores across runs
  - *Mitigation*: Use consistent model (reflector model), detailed prompts, 1-5 rubric with clear definitions
  - *When*: During implementation, tune prompts if scores are inconsistent

### Critical + Known
- **Eval runtime**: Real API calls are slow (~2-5 min for full suite)
  - *Mitigation*: Target 10 cases (not 50), parallel test execution
  - *When*: Monitor during implementation

### Non-Critical
- **Judge false positives/negatives**: May pass bad outputs or fail good ones
  - *Mitigation*: Pass threshold at 3/5 (acceptable), manually review failures
  - *Deferral*: Expand eval coverage after validating initial cases work

---

## Iteration Plan

### Iteration 1: Tier 1 - Fast Unit Tests with TestModel (COMPLETE)

All 202 tests converted to use TestModel + Agent.override(). Runs in 0.42s.

---

### Iteration 2: Tier 2 Foundation - Core Infrastructure (NOW)
**Goal**: Create LLM-as-judge evaluator and data models

**Tasks**:
1. Create `nanoagent/evals/__init__.py` - exports
2. Create `nanoagent/evals/models.py` - EvalDimension enum, EvalScore schema (~30 LOC)
3. Create `nanoagent/evals/judge.py` - evaluator agent with dimension-specific prompts (~40 LOC)
4. Modify `pyproject.toml` - add eval marker, default skip with `addopts = "-m 'not eval'"`

**Data Models** (`models.py`):
```python
class EvalDimension(str, Enum):
    PLAN_QUALITY = "plan_quality"
    REFLECTION_ACCURACY = "reflection_accuracy"
    EXECUTION_CORRECTNESS = "execution_correctness"
    CONVERGENCE_BEHAVIOR = "convergence_behavior"

class EvalScore(BaseModel):
    dimension: EvalDimension
    score: int = Field(..., ge=1, le=5)
    reasoning: str = Field(..., min_length=10)
    pass_threshold: int = Field(default=3)

    @property
    def passed(self) -> bool:
        return self.score >= self.pass_threshold
```

**Evaluator** (`judge.py`):
```python
evaluator = Agent(
    model=get_settings().reflector_model,
    output_type=EvalScore,
    system_prompt=BASE_SYSTEM_PROMPT,
)

DIMENSION_PROMPTS = {
    EvalDimension.PLAN_QUALITY: "Evaluate task decomposition: specific, actionable, complete?",
    EvalDimension.REFLECTION_ACCURACY: "Evaluate reflection: real gaps, correct done flag?",
    # ...
}

async def evaluate(dimension: EvalDimension, prompt: str) -> EvalScore:
    full_prompt = f"{DIMENSION_PROMPTS[dimension]}\n\n{prompt}"
    result = await evaluator.run(full_prompt)
    return result.output
```

---

### Iteration 3: Tier 2 Integration - Eval Test Cases (NOW)
**Goal**: Create test cases and eval test files for all 4 dimensions

**Tasks**:
1. Create `nanoagent/tests/evals/__init__.py`
2. Create `nanoagent/tests/evals/cases.py` - 10 test cases (2-3 per dimension)
3. Create `nanoagent/tests/evals/plan_quality_eval.py` - plan quality evals
4. Create `nanoagent/tests/evals/reflection_accuracy_eval.py` - reflection evals
5. Create `nanoagent/tests/evals/execution_correctness_eval.py` - execution evals
6. Create `nanoagent/tests/evals/convergence_eval.py` - convergence evals

**Test Cases** (`cases.py`):
```python
PLAN_QUALITY_CASES = [
    {"name": "simple_calculation", "goal": "Calculate factorial of 5", ...},
    {"name": "multi_step", "goal": "Build REST API with auth", ...},
    {"name": "ambiguous", "goal": "Make something cool with AI", ...},
]

REFLECTION_ACCURACY_CASES = [
    {"name": "complete_goal", "expected_done": True, ...},
    {"name": "incomplete_goal", "expected_done": False, ...},
]
# ... etc
```

**Eval Test Pattern**:
```python
@pytest.mark.eval
@pytest.mark.asyncio
@pytest.mark.parametrize("case", PLAN_QUALITY_CASES, ids=[c["name"] for c in PLAN_QUALITY_CASES])
async def test_plan_quality(case: dict) -> None:
    plan = await plan_tasks(case["goal"])

    eval_prompt = f"Goal: {case['goal']}\nPlan: {plan.tasks}\n..."
    score = await evaluate(EvalDimension.PLAN_QUALITY, eval_prompt)

    assert score.passed, f"Plan quality: {score.score}/5 - {score.reasoning}"
```

---

### Iteration 4: Tier 2 Polish - Testing & Documentation (NOW)
**Goal**: Unit tests for eval framework and usage documentation

**Tasks**:
1. Create `nanoagent/evals/models_test.py` - test EvalScore schema
2. Create `nanoagent/evals/judge_test.py` - test judge with TestModel override
3. Document eval usage in README or DESIGN.md
4. Validate all evals pass with real LLM calls
5. Tune pass thresholds if needed

---

## Reference: pydantic-evals API (Alternative to DeepEval)

### Core Components

**Case**: Single test case definition
```python
from pydantic_evals import Case

case = Case(
    name='simple_task',              # Test name (for reporting)
    inputs='user input',              # What you pass to the function
    expected_output='expected',       # What you expect back
    metadata={'difficulty': 'easy'}   # Optional context
)
```

**Dataset**: Collection of cases + evaluators (reusable across unit tests and evals)
```python
from pydantic_evals import Dataset
from pydantic_evals.evaluators import IsInstance, Contains, MaxDuration, LLMJudge

dataset = Dataset(
    cases=[case1, case2, case3],      # Reuse same cases for unit tests & evals
    evaluators=[
        IsInstance(type_name='str'),  # Check type
        Contains(value='keyword'),    # Check content
        MaxDuration(seconds=2.0),     # Check performance
    ]
)
```

**Evaluators**: Built-in validation rules (run in order, fail-fast)

| Evaluator | Use Case | Cost |
|-----------|----------|------|
| `EqualsExpected()` | Exact match with expected_output | Free |
| `IsInstance(type_name='str')` | Type checking | Free |
| `Contains(value='x')` | String/list contains check | Free |
| `MaxDuration(seconds=2.0)` | Performance validation | Free |
| `LLMJudge(rubric='...')` | Subjective quality (e.g., "response is helpful") | API calls |
| Custom `Evaluator` | Domain-specific logic | Free |

**EvaluationReport**: Results from running dataset
```python
report = dataset.evaluate_sync(my_function)

# Access results
print(f"Pass rate: {report.pass_rate}")              # 0.0-1.0
print(f"Averages: {report.averages()}")              # Per-evaluator stats
report.print(include_input=True, include_output=True) # Pretty-print results
```

### Usage Patterns

**Pattern 1: Unit Testing (Deterministic, Fast)**
```python
# Use only free evaluators; run in CI/CD
dataset = Dataset(
    cases=[Case(inputs='hello', expected_output='HELLO')],
    evaluators=[
        IsInstance(type_name='str'),
        Contains(value='HELLO'),
    ]
)
report = dataset.evaluate_sync(uppercase_function)
assert report.pass_rate == 1.0  # Blocks CI if fails
```

**Pattern 2: LLM Evaluation (Flexible, Slow)**
```python
# Add LLMJudge for subjective dimensions; run manually with real models
dataset = Dataset(
    cases=[Case(inputs='explain quantum computing', expected_output='...')],
    evaluators=[
        IsInstance(type_name='str'),           # Fast deterministic check first
        LLMJudge(                              # Then slow LLM-based check
            rubric='Explanation is clear and accurate',
            include_input=True,
        ),
    ]
)
# Run with: ALLOW_MODEL_REQUESTS=true pytest -m eval
report = dataset.evaluate_sync(my_agent.run)
report.print()
```

**Pattern 3: Sharing Cases Between Unit Tests & Evals**
```python
# datasets/task_planner_cases.py
from pydantic_evals import Case

task_planner_cases = [
    Case(
        name='simple_goal',
        inputs={'goal': 'Build a calculator'},
        expected_output=TaskPlanOutput(
            tasks=['Implement addition', 'Implement subtraction'],
            questions=[]
        ),
        metadata={'complexity': 'low'}
    ),
    # ... more cases
]

# In *_test.py (unit test with mocks - fast, deterministic)
@pytest.mark.parametrize('case', task_planner_cases)
def test_task_planner(case):
    dataset = Dataset(cases=[case], evaluators=[IsInstance(...)])
    report = dataset.evaluate_sync(mock_planner)
    assert report.pass_rate == 1.0

# In evals/test_task_planner_eval.py (eval test - real LLM, flexible)
@pytest.mark.eval
def test_task_planner_eval():
    dataset = Dataset(
        cases=task_planner_cases,
        evaluators=[
            IsInstance(...),
            LLMJudge(rubric='Tasks are independent and actionable'),
        ]
    )
    report = dataset.evaluate_sync(real_planner)
    assert report.pass_rate >= 0.7  # Flexible assertion (not 100%)
```

### Custom Evaluators

For domain-specific validation logic:
```python
from pydantic_evals.evaluators import Evaluator, EvaluatorContext

class TasksAreIndependent(Evaluator):
    """Check that tasks don't have sequential dependencies."""

    def evaluate(self, ctx: EvaluatorContext) -> float:
        output = ctx.output  # TaskPlanOutput

        # Business logic: tasks should be parallelizable
        if len(output.tasks) <= 1:
            return 1.0  # Single task is always independent

        # Check for sequential language
        sequential_markers = ['then', 'after', 'once', 'first', 'second']
        task_text = ' '.join(output.tasks).lower()

        for marker in sequential_markers:
            if marker in task_text:
                return 0.5  # Partial credit

        return 1.0  # All clear

# Use in dataset
dataset = Dataset(
    cases=[...],
    evaluators=[
        IsInstance(...),           # Fast check
        TasksAreIndependent(),     # Custom logic
        LLMJudge(...),             # Expensive LLM check last
    ]
)
```

### Official Documentation
- Pydantic Evals on GitHub: https://github.com/pydantic/pydantic-ai/tree/main/docs/evals
- Official docs: https://docs.pydantic.dev/evals/ (when published)

---

## Deferred Items

- **Eval dashboards/tracking**: Defer to separate monitoring feature
- **Cost optimization/sampling**: Defer to when at production scale
- **Continuous eval monitoring**: Defer to ops/monitoring phase
- **More eval cases**: Start with 10, expand based on coverage gaps

---

## Next Steps

1. **Implement Iteration 2**: Create models.py, judge.py, register pytest marker
2. **Implement Iteration 3**: Create cases.py and 4 eval test files
3. **Implement Iteration 4**: Add judge unit tests, documentation
4. **Validate**: Run `pytest -m eval` and tune thresholds

---

## File Changes Summary

### Tier 1 (COMPLETE) - ~50 LOC

All tests converted. No changes needed.

### Tier 2 (NOW) - ~130 LOC

**Eval Framework** (`nanoagent/evals/`):
- `__init__.py` - exports (~5 LOC)
- `models.py` - EvalDimension, EvalScore (~30 LOC)
- `models_test.py` - schema unit tests (~10 LOC)
- `judge.py` - evaluator + prompts (~40 LOC)
- `judge_test.py` - judge unit tests with TestModel (~15 LOC)

**Eval Tests** (`nanoagent/tests/evals/`):
- `__init__.py`
- `cases.py` - test case data (not counted as code)
- `plan_quality_eval.py` (~15 LOC)
- `reflection_accuracy_eval.py` (~15 LOC)
- `execution_correctness_eval.py` (~15 LOC)
- `convergence_eval.py` (~15 LOC)

**Modify**:
- `pyproject.toml` - add eval marker + default skip (~3 lines)

**No new dependencies** - uses existing Pydantic AI
