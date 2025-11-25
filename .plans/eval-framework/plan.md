# Eval Framework Feature Plan

## Overview
Two-tier testing strategy: fast unit tests (Tier 1) + quality evaluation for prompt/model iteration (Tier 2).

**Problem**: Current tests using `ALLOW_MODEL_REQUESTS=true` are slow (5+ min) and flaky. Additionally, there's no systematic way to iterate on prompts/models and measure quality improvements.

**Solution**:
- **Tier 1 (Now)**: Use Pydantic AI's built-in `TestModel` + `Agent.override()` for fast, deterministic unit tests
- **Tier 2 (Deferred)**: Use DeepEval for quality evaluation and prompt/model iteration

---

## Success Criteria

### Tier 1 (Now)
- [ ] All 24 tests converted to use TestModel + Agent.override()
- [ ] `pytest nanoagent/` runs in <1s, 100% passing
- [ ] No new dependencies added
- [ ] Total LOC change: ~50 LOC

### Tier 2 (Deferred)
- [ ] DeepEval added as dependency
- [ ] Eval tests created for TaskPlanner, Executor, Reflector
- [ ] G-Eval metrics for subjective quality assessment
- [ ] Evals run with `ALLOW_MODEL_REQUESTS=true pytest nanoagent/evals/ -m eval`

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

### Tier 2: Quality Evaluation (Framework Comparison)

| Framework | Verdict | Reason |
|-----------|---------|--------|
| **DeepEval** | ✅ Recommended | Research-backed G-Eval metrics, pytest-style, @observe decorators, excellent Pydantic AI integration |
| **pydantic-evals** | ⚠️ Alternative | Native Pydantic AI ecosystem, LLMJudge, Logfire integration |
| **DSPy** | ❌ Overkill | Auto-optimization needs 50+ examples; manual iteration sufficient for <500 LOC framework |
| **Ragas** | ❌ RAG-focused | Excellent for retrieval, but not agent-focused |
| **Braintrust** | ❌ Enterprise | Platform-heavy, overkill for current needs |

### Why DeepEval for Tier 2?

1. **Research-backed metrics** - G-Eval framework with two-phase evaluation (reasoning steps → scoring)
2. **Excellent Pydantic AI integration** - @observe decorators work seamlessly with agents
3. **Component-level evaluation** - Matches TaskPlanner→Executor→Reflector architecture
4. **pytest-compatible** - Native CI/CD integration
5. **Agent-specific metrics** - Task completion, tool correctness built-in
6. **Low setup friction** - Minimal code changes

### pydantic-evals Capabilities (for reference)

- **LLMJudge**: Evaluate subjective quality (is the plan sensible? is the reflection useful?)
- **Deterministic evaluators**: EqualsExpected, IsInstance, Contains, MaxDuration
- **Custom evaluators**: Domain-specific logic via Evaluator base class
- **Span-based evaluation**: Verify internal agent behavior (tool calls, execution flow)
- **Logfire integration**: Native observability

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
└── evals/                          # Tier 2: Quality evaluation (DeepEval, deferred)
    ├── __init__.py
    ├── conftest.py
    └── ...
```

**Run patterns**:
```bash
# Tier 1: Fast unit tests (default, CI-friendly)
pytest nanoagent/                          # <1s, 100% passing, deterministic

# Tier 2: Quality evals (deferred - future implementation with DeepEval)
ALLOW_MODEL_REQUESTS=true pytest nanoagent/evals/ -m eval
```

### Tier 1: Unit Testing Philosophy (TestModel)

```python
from pydantic_ai.models.test import TestModel

async def test_executor_structured_output(self):
    # Fast, deterministic, no API calls
    with executor.override(model=TestModel()):
        result = await execute_task("test task")
        assert isinstance(result, ExecutionResult)
        assert result.status in ["success", "error"]
```

- Validate agent outputs match schema
- Validate deterministic logic (orchestration, context passing)
- Run on every commit, block deployment on failure
- No external dependencies beyond pydantic-ai

### Tier 2: Quality Evaluation Philosophy (DeepEval - Deferred)

```python
from deepeval import evaluate
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase

@pytest.mark.eval
async def test_task_planner_quality():
    result = await task_planner.run("Build a REST API")

    test_case = LLMTestCase(
        input="Build a REST API",
        actual_output=result.model_dump_json(),
    )

    metric = GEval(
        name="plan_quality",
        criteria="Is the task decomposition logical and complete?",
        evaluation_steps=[
            "Check if all major components are identified",
            "Verify tasks are actionable and independent",
        ]
    )

    assert metric.measure(test_case).score > 0.7
```

- Validate subjective quality dimensions
- Use research-backed G-Eval metrics
- Component-level tracing with @observe decorators
- Run manually for prompt/model iteration

---

## Risk Analysis

### Critical + Unknown
- **Mock fixture realism**: Will mocked responses be realistic enough?
  - *Mitigation*: Use actual successful API responses as fixture templates
  - *When*: During implementation, verify against original behavior

### Critical + Known
- **Pydantic AI API changes**: Already identified `result_type` → `output_type`
  - *Mitigation*: Already fixed in executor tests
  - *When*: Before implementation

### Non-Critical
- **Eval script coverage**: Not all edge cases covered in evals
  - *Mitigation*: Start with happy path + 2-3 critical scenarios
  - *Deferral*: Expand eval coverage in future feature

---

## Iteration Plan

### Iteration 1: Tier 1 - Fast Unit Tests with TestModel (NOW)
**Goal**: Convert all 24 tests to use TestModel + Agent.override() for fast, deterministic execution

**Tasks**:
1. Convert `executor_test.py` - 4 tests
2. Convert `reflector_test.py` - 7 tests
3. Convert `task_planner_test.py` - 5 tests
4. Convert `e2e_test.py` - 6 tests
5. Convert `orchestration_test.py` - 2 tests
6. Remove `require_real_api_key` fixture from unit tests
7. Verify `pytest nanoagent/` runs in <1s

**Implementation Pattern**:
```python
from pydantic_ai.models.test import TestModel

class TestExecutor:
    @pytest.mark.asyncio
    async def test_executor_structured_output(self):
        # Before: Real API call (slow, flaky)
        # @pytest.mark.usefixtures("require_real_api_key")
        # result = await execute_task("Search for Python info")

        # After: TestModel (fast, deterministic)
        with executor.override(model=TestModel()):
            result = await execute_task("Search for Python info")
            assert isinstance(result, ExecutionResult)
```

**Success Criteria**:
- [ ] All 24 tests converted to use TestModel
- [ ] `pytest nanoagent/` runs in <1s, 100% passing
- [ ] No new dependencies added
- [ ] Total LOC change: ~50 LOC

**Outcome**: Fast, reliable unit tests for CI/CD

---

### Iteration 2: Tier 2 - Quality Evaluation with DeepEval (DEFERRED)
**Goal**: Create quality evaluation suite for prompt/model iteration

**Tasks** (when implemented):
1. `uv add deepeval`
2. Create `nanoagent/evals/` directory structure
3. Create eval tests with G-Eval metrics for each agent
4. Add @observe decorators for component-level tracing
5. Document eval usage patterns

**Implementation Pattern** (DeepEval):
```python
from deepeval import evaluate
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase

@pytest.mark.eval
@pytest.mark.asyncio
async def test_task_planner_quality():
    result = await task_planner.run("Build a REST API with authentication")

    test_case = LLMTestCase(
        input="Build a REST API with authentication",
        actual_output=result.model_dump_json(),
    )

    metric = GEval(
        name="plan_quality",
        criteria="Is the task decomposition logical, complete, and actionable?",
        evaluation_steps=[
            "Check if all major components are identified",
            "Verify tasks are independent and parallelizable",
            "Confirm each task is specific enough to execute",
        ]
    )

    result = metric.measure(test_case)
    assert result.score > 0.7, f"Plan quality score {result.score} below threshold"
```

**Run evals**:
```bash
# Run quality evals with real models
ALLOW_MODEL_REQUESTS=true pytest nanoagent/evals/ -m eval -v
```

**Outcome**: Systematic quality measurement for prompt/model iteration

---

### Iteration 3: Documentation (DEFERRED)
**Goal**: Clear usage patterns for two-tier testing

**Tasks**:
1. Document Tier 1 (TestModel) usage patterns
2. Document Tier 2 (DeepEval) usage patterns
3. Explain when to use each tier
4. Provide examples for custom evaluators

**Outcome**: Teams understand and can extend two-tier testing approach

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

- **Tier 2 (DeepEval)**: Quality evaluation for prompt/model iteration
- **LLM-as-judge scoring**: Defer to Tier 2 implementation
- **Eval dashboards/tracking**: Defer to separate monitoring feature
- **Cost optimization/sampling**: Defer to when at production scale
- **Continuous eval monitoring**: Defer to ops/monitoring phase

---

## Next Steps

1. **Implement Tier 1**: Convert all 24 tests to use TestModel + Agent.override()
2. **Verify**: Ensure `pytest nanoagent/` runs in <1s, 100% passing
3. **Later**: Implement Tier 2 with DeepEval when quality evaluation is needed

---

## File Changes Summary

### Tier 1 (Now) - ~50 LOC total

**Modified**:
- `nanoagent/core/executor_test.py` - Add TestModel override to 4 tests (~10 LOC)
- `nanoagent/core/reflector_test.py` - Add TestModel override to 7 tests (~15 LOC)
- `nanoagent/core/task_planner_test.py` - Add TestModel override to 5 tests (~10 LOC)
- `nanoagent/tests/integration/e2e_test.py` - Add TestModel override to 6 tests (~10 LOC)
- `nanoagent/tests/integration/orchestration_test.py` - Add TestModel override to 2 tests (~5 LOC)

**No new files or dependencies required**

### Tier 2 (Deferred) - ~200 LOC when implemented

**Will Create**:
- `nanoagent/evals/__init__.py`
- `nanoagent/evals/conftest.py` - Setup eval marker, fixtures
- `nanoagent/evals/task_planner_eval_test.py`
- `nanoagent/evals/executor_eval_test.py`
- `nanoagent/evals/reflector_eval_test.py`
- `nanoagent/evals/e2e_eval_test.py`

**Will Add**:
- `deepeval` dependency (when Tier 2 is implemented)
