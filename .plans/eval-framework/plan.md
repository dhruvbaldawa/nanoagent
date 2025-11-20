# Eval Framework Feature Plan

## Overview
Implement hybrid testing: fast mocked unit tests (default) + opt-in eval scripts for real LLM validation.

**Problem**: Current tests using `ALLOW_MODEL_REQUESTS=true` are slow (5+ min) and flaky. Need to:
- Make default `uv run pytest` fast and reliable (<1s, 100% pass)
- Validate real LLM behavior via separate, optional eval scripts

**Solution**: Separate deterministic unit tests (mocked) from stochastic eval scripts (real models), following industry best practices.

---

## Success Criteria
- [ ] Default `uv run pytest` runs in <1s, 100% passing, zero flakiness
- [ ] All 24 currently-skipped/failing tests converted to mocked tests
- [ ] Eval scripts created for validating real LLM behavior (opt-in)
- [ ] Behavioral assertions: validates LLM achieves goals, not exact outputs
- [ ] Implementation <200 LOC (minimal overhead)

---

## Research Findings

### Official Library Investigation
✅ **`pydantic-evals` exists** - separate official package for Pydantic AI evaluations

**Key Capabilities** (from official docs):
- `Case` - Define test cases with inputs, expected_output, metadata
- `Dataset` - Manage test case collections with evaluators
- **Built-in Evaluators**:
  - `EqualsExpected()` - Exact output match
  - `IsInstance()` - Type validation
  - `Contains()` - String content validation
  - `MaxDuration()` - Performance/timing checks
  - `LLMJudge()` - Custom LLM-based evaluation with rubrics
  - Custom evaluators supported via `Evaluator` base class
- Single API for both unit test mocking and real eval validation

**Perfect for our use case**:
- Deterministic checks (IsInstance, Contains) for unit tests (fast, no API)
- Can swap in real LLM-as-judge when using real models (slow, costly)
- Exact same dataset/case structure for both test types

### Available Options
1. **`pydantic-evals` package** ✅ (RECOMMENDED)
   - Official Pydantic product
   - Zero external dependencies beyond existing stack
   - Built-in evaluators + LLMJudge for both mocking and real validation
   - Elegant API: same code for unit tests (mocked) and eval scripts (real)
   - Effort: 2-3 hours

2. **Braintrust + AutoEvals**
   - Richer platform features but adds platform dependency
   - Overkill for current needs
   - Can integrate later if needed

3. **Custom pytest fixtures + unittest.mock**
   - More code to maintain
   - No LLMJudge integration

### Recommendation
**`pydantic-evals` package** for this feature:
- Official, maintained by Pydantic team
- Designed for exactly this hybrid testing pattern
- Minimal setup, maximum flexibility
- Clean API across mock and real LLM scenarios

---

## Architecture Decision

### Test Structure (Using `pydantic-evals`)
```
nanoagent/
├── core/
│   ├── executor_test.py            # Unit tests (fast, mocked, deterministic, CI gate)
│   ├── executor_eval_test.py       # Eval tests with @pytest.mark.eval
│   ├── reflector_test.py
│   ├── reflector_eval_test.py
│   ├── task_planner_test.py
│   ├── task_planner_eval_test.py
│   └── ...
└── evals/
    ├── __init__.py
    ├── conftest.py                 # Pytest fixtures + eval marker config
    └── datasets/                   # Shared test case definitions
        ├── executor_cases.py
        ├── reflector_cases.py
        ├── task_planner_cases.py
        └── e2e_cases.py
```

**Dual-mode operation**:
```bash
# Default: Run only unit tests (fast, CI-friendly)
pytest nanoagent/                          # 202 tests, <1s, deterministic

# Run evals as pytest suite (with real models)
ALLOW_MODEL_REQUESTS=true pytest -m eval   # 4 eval suites, ~60s, flexible assertions

# Or run specific eval test
ALLOW_MODEL_REQUESTS=true pytest nanoagent/core/executor_eval_test.py -v

# Skip all evals (useful for CI)
pytest nanoagent/ -m "not eval"
```

### Testing Philosophy (Using `pydantic-evals`)
- **Unit Tests** (deterministic evaluators):
  ```python
  # Same Case/Dataset structure for both!
  dataset = Dataset(
    cases=[Case(inputs='...', expected_output=TaskPlanOutput(...))],
    evaluators=[
      IsInstance(type_name='TaskPlanOutput'),  # Schema validation
      Contains(value='task'),  # Content check
    ]
  )
  report = dataset.evaluate_sync(planner.plan)  # Mock or real
  ```
  - Validate agent outputs match schema
  - Validate deterministic logic (orchestration, context passing)
  - Use `IsInstance()`, `Contains()`, `MaxDuration()` (fast, free, no LLM calls)
  - Run on every commit, block deployment on failure

- **Eval Scripts** (with LLMJudge):
  ```python
  # Same dataset definition, add LLMJudge evaluator!
  dataset = Dataset(
    cases=[...],  # Same cases as unit tests
    evaluators=[
      IsInstance(...),  # Keep deterministic checks
      LLMJudge(rubric='Plan includes reasonable task breakdown'),  # Real LLM
    ]
  )
  ```
  - Validate real LLM behavior across scenarios
  - Assert goal achievement (task count reasonable, completion detection works)
  - Use `LLMJudge()` for subjective dimensions (requires API calls)
  - Run manually with `ALLOW_MODEL_REQUESTS=true python nanoagent/evals/scripts/eval_*.py`
  - Inform development; don't block CI

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

### Iteration 1: Setup & Unit Test Integration (Foundation)
**Goal**: Add `pydantic-evals` package and convert tests to use Dataset/Case/Evaluators

Tasks:
1. Add `pydantic-evals` to uv.lock: `uv add pydantic-evals`
2. Create `nanoagent/evals/conftest.py` - Mock agent fixtures for tests
3. Create `nanoagent/evals/datasets/executor_cases.py` - ExecutionResult test cases
4. Convert executor_test.py to use Dataset + IsInstance/Contains evaluators
5. Create reflector/task_planner/e2e test cases similarly
6. Update all 24 tests to use pydantic-evals (swap real agents for mocks)
7. Verify all tests pass in <1s

**Implementation Pattern**:
```python
# executor_test.py
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import IsInstance, Contains
from nanoagent.evals.datasets.executor_cases import executor_cases

@pytest.mark.parametrize('case', executor_cases)
def test_executor_with_case(case):
    dataset = Dataset(
        cases=[case],
        evaluators=[
            IsInstance(type_name='ExecutionResult'),
            Contains(value='success') if case.metadata.get('expects_success') else Contains(value='error'),
        ]
    )
    report = dataset.evaluate_sync(mock_executor.execute_task)
    assert report.pass_rate == 1.0
```

**Outcome**: `uv run pytest` runs full suite in <1s, 100% passing, zero flakiness

### Iteration 2: Eval Tests with LLMJudge (Integration)
**Goal**: Create pytest-compatible eval suite using same test cases + real LLM validation

Tasks:
1. Create `nanoagent/evals/conftest.py` - Setup `@pytest.mark.eval` marker, LLM fixtures
2. Create `nanoagent/evals/datasets/*.py` - Shared test case definitions
3. Create `nanoagent/core/executor_eval_test.py` - Use LLMJudge for execution quality
4. Create `nanoagent/core/reflector_eval_test.py` - Validate completion detection
5. Create `nanoagent/core/task_planner_eval_test.py` - Use LLMJudge for plan quality
6. Create `nanoagent/tests/integration/e2e_eval_test.py` - Validate orchestration quality

**Implementation Pattern**:
```python
# nanoagent/core/task_planner_eval_test.py
import pytest
from pydantic_evals import Dataset
from pydantic_evals.evaluators import IsInstance, LLMJudge
from nanoagent.evals.datasets.task_planner_cases import task_planner_cases
from nanoagent.core.task_planner import plan_tasks

@pytest.mark.eval  # Mark as eval test (skip by default, run with -m eval)
@pytest.mark.asyncio
async def test_task_planner_with_lljudge():
    """Validate task planner with real LLM evaluation."""
    dataset = Dataset(
        cases=task_planner_cases,
        evaluators=[
            IsInstance(type_name='TaskPlanOutput'),  # Fast check first
            LLMJudge(
                rubric='Plan breaks goal into 5-15 reasonable tasks; tasks are independent and actionable',
                include_input=True,
            ),  # Slow but flexible LLM check
        ]
    )

    report = dataset.evaluate_sync(plan_tasks)

    # Assert both deterministic (100%) and LLM-based (>70%) pass rates
    assert report.pass_rate >= 0.7, f"LLM eval pass rate {report.pass_rate} below 70%"
    # Print detailed report for investigation
    report.print(include_input=True, include_output=True)
```

**Run evals**:
```bash
# Run with real LLM evaluation
ALLOW_MODEL_REQUESTS=true pytest nanoagent/evals -m eval -v

# Or specific eval only
ALLOW_MODEL_REQUESTS=true pytest nanoagent/evals/test_task_planner_eval.py -v

# Skip evals (default for CI)
pytest nanoagent/ -m "not eval"
```

**Outcome**: Pytest-compatible eval suite; can run standalone or as part of test suite

### Iteration 3: Documentation (Polish)
**Goal**: Clear usage patterns for hybrid testing

Tasks:
1. Add eval section to README with examples
2. Document when to use unit tests (CI, fast, deterministic) vs evals (manual, flexible)
3. Create example eval results and how to interpret them
4. Document custom evaluator pattern for specialized checks

**Outcome**: Teams understand and can extend hybrid testing approach

---

## How pydantic-evals Works (Reference for Future)

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

- **LLM-as-judge scoring**: Defer to when eval scripts prove the need
- **Eval dashboards/tracking**: Defer to separate monitoring feature
- **Cost optimization/sampling**: Defer to when at production scale
- **Braintrust integration**: Defer to if/when platform monitoring needed
- **Continuous eval monitoring**: Defer to ops/monitoring phase

---

## Next Steps

1. **Confirm approach**: Is pytest fixtures + unittest.mock acceptable?
2. **Create tasks**: Generate pending/*.md files for each iteration
3. **Implement**: Follow TDD for each test conversion

---

## File Changes Summary

**Modified**:
- nanoagent/core/executor_test.py (~20 LOC added for pydantic-evals integration)
- nanoagent/core/reflector_test.py (~25 LOC added for pydantic-evals integration)
- nanoagent/core/task_planner_test.py (~20 LOC added for pydantic-evals integration)
- nanoagent/tests/integration/e2e_test.py (~15 LOC added for pydantic-evals integration)

**Created - Eval Framework**:
- nanoagent/evals/__init__.py (~5 LOC)
- nanoagent/evals/conftest.py (~20 LOC) - Setup eval marker, fixtures
- nanoagent/evals/datasets/executor_cases.py (~30 LOC)
- nanoagent/evals/datasets/reflector_cases.py (~30 LOC)
- nanoagent/evals/datasets/task_planner_cases.py (~30 LOC)
- nanoagent/evals/datasets/e2e_cases.py (~30 LOC)

**Created - Eval Tests**:
- nanoagent/core/executor_eval_test.py (~35 LOC)
- nanoagent/core/reflector_eval_test.py (~35 LOC)
- nanoagent/core/task_planner_eval_test.py (~35 LOC)
- nanoagent/tests/integration/e2e_eval_test.py (~35 LOC)

**Total LOC Impact**: ~385 LOC
- Unit test modifications: 80 LOC
- Eval framework (conftest + datasets): 145 LOC
- Eval tests: 140 LOC
- Plus pydantic-evals dependency (new package)
