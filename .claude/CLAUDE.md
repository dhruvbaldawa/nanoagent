# Nanoagent Project Guidelines

## Project Context

Lightweight multi-agent framework (<500 LOC) using Pydantic AI for autonomous task execution. Goal: prove that planning → execution → reflection cycles work reliably with minimal code.

## Development Setup

### Python Environment

- **Python:** 3.14
- **Package Manager:** uv (2025 standard)
- **Quality Tools:** ruff (line-length 120), basedpyright (strict), pytest + pytest-asyncio
- **Pre-commit:** Configured with sync-with-uv to eliminate version drift

### Common Commands

```bash
uv sync                # Install dependencies from uv.lock
uv run ruff format          # Format code with ruff
uv run ruff check            # Lint with ruff
uv run basedpyright       # Type check with basedpyright
uv run pytest            # Run tests with pytest
```

### Key Principles

- uv auto-manages `.venv` - no manual activation needed
- `uv.lock` is committed for reproducibility
- Use `--group dev` for dev dependencies (pytest, ruff, basedpyright, pre-commit)
- Tests live next to source code (`*_test.py` pattern)
- Pre-commit syncs versions from uv.lock automatically

## Project Structure

```
nanoagent/
├── core/              # Core orchestration components
│   ├── orchestrator.py / orchestrator_test.py
│   ├── task_planner.py / task_planner_test.py
│   ├── executor.py / executor_test.py
│   ├── reflector.py / reflector_test.py
│   ├── todo_manager.py / todo_manager_test.py
│   └── stream_manager.py / stream_manager_test.py
├── models/            # Pydantic data models
│   ├── schemas.py / schemas_test.py
└── tools/             # Tool registry and implementations
    ├── registry.py / registry_test.py
    └── builtin.py / builtin_test.py
```

## TDD Approach (CRITICAL)

Every task MUST follow Test-Driven Development:
1. Write failing test that validates desired functionality
2. Run test to confirm it fails as expected
3. Write ONLY enough code to make the test pass
4. Run test to confirm success
5. Refactor if needed while keeping tests green

**Tests are not optional.** No component is "done" without passing tests.

## LOC Budget

- **Target:** <500 LOC for core framework (excluding tests)
- **Current Milestone 1:** ~290 LOC budgeted
- **Track carefully:** LOC counter must stay under budget

## Critical Risks Being Validated

**Milestone 1 validates:**
1. **Pydantic AI Structured Outputs** - Do TaskPlanOutput, ExecutionResult, ReflectionOutput parse reliably?
2. **Agent Coordination** - Does context pass correctly between planner → executor → reflector?
3. **Reflection Quality** - Does reflector identify gaps and suggest sensible next steps?

## Agent Implementation Patterns

### Pydantic AI Agent Structure

```python
from pydantic_ai import Agent
from nanoagent.models.schemas import OutputType

agent = Agent(
    model="anthropic:claude-sonnet-4-0",
    result_type=OutputType,
    system_prompt="Clear instructions...",
)
```

### With Dependencies

```python
from pydantic_ai import Agent, RunContext
from pydantic import BaseModel

class AgentDeps(BaseModel):
    # Dependencies here
    pass

agent = Agent(
    model="anthropic:claude-sonnet-4-0",
    result_type=OutputType,
    deps_type=AgentDeps,
    system_prompt="...",
)

@agent.tool
async def tool_name(ctx: RunContext[AgentDeps], param: str) -> str:
    # Access deps via ctx.deps
    return result
```

## Testing Patterns

### Unit Tests (Pure Logic)
```python
def test_component_behavior():
    instance = Component()
    result = instance.method("input")
    assert result == expected
```

### Agent Tests (Real LLM Calls)
```python
@pytest.mark.asyncio
async def test_agent_structured_output():
    result = await agent.run("test input")
    assert isinstance(result.data, ExpectedOutput)
    assert result.data.field == expected_value
```

**IMPORTANT:** Agent tests use REAL API calls, not mocks. We're validating that Pydantic AI works, not testing our mocks.

## Deferred to Future Milestones

- Persistence (in-memory sufficient for M1)
- Human-in-the-loop (not needed for autonomous validation)
- MCP integration (extension point)
- Multiple tool implementations (minimal set in M1)
- Automated orchestration loop (manual POC in M1)

## References

- **DESIGN.md** - Architecture and agent workflow
- **.plans/nanoagent/plan.md** - Milestone planning and risk analysis
- **.plans/nanoagent/plan.md § Research Findings** - Validated configs for pre-commit, quality tools

## When Stuck

1. Check plan.md § Research Findings for validated approaches
2. Read DESIGN.md for architecture clarification
3. Review existing tests for patterns
4. Ask Dhruv if uncertain about architectural decisions
