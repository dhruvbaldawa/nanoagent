# Nanoagent

A lightweight multi-agent framework (<500 LOC) using Pydantic AI for autonomous task execution and planning.

## Features

- **Pydantic AI Integration**: Structured outputs for reliable agent coordination
- **Planning → Execution → Reflection Cycles**: Autonomous goal decomposition and gap detection
- **Pluggable Tools**: Extensible tool registry for custom capabilities
- **Type-Safe**: Strict type checking with basedpyright

## Getting Started

### Prerequisites

- Python 3.14+
- uv (2025 standard package manager)
- API keys for at least one LLM provider (Anthropic, OpenAI, OpenRouter, etc.)

### Installation

```bash
uv sync
```

### Configuration

Nanoagent supports multiple LLM providers through Pydantic AI. Configure which model each agent uses via environment variables:

```bash
# Required: Specify model for each agent (format: 'provider:model-name')
export TASK_PLANNER_MODEL="anthropic:claude-sonnet-4-5-20250514"
export EXECUTOR_MODEL="openrouter:anthropic/claude-3.5-sonnet"
export REFLECTOR_MODEL="openai:gpt-4o"

# Set API keys for your chosen providers
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."
export OPENROUTER_API_KEY="sk-or-..."  # Only needed if using OpenRouter
```

**Supported Providers:**
- `anthropic`: Claude models (requires ANTHROPIC_API_KEY)
- `openai`: GPT models (requires OPENAI_API_KEY)
- `openrouter`: Multi-provider via OpenRouter (requires OPENROUTER_API_KEY)
- `google-gemini`: Google Gemini models (requires GOOGLE_API_KEY)
- `groq`: Groq models (requires GROQ_API_KEY)
- And 9+ other providers supported by Pydantic AI

**Model Format:**
Each model must be specified as `provider:model-identifier`. Examples:
- `anthropic:claude-sonnet-4-5-20250514`
- `openai:gpt-4o`
- `openrouter:anthropic/claude-3.5-sonnet`
- `openrouter:openai/gpt-4-turbo`
- `google-gemini:gemini-1.5-pro`

**Per-Agent Configuration:**
You can use different models for different agents. For example:
- Use a fast/cheap model for TaskPlanner and Executor
- Use a capable model for Reflector (critical decision-making)

```bash
# Cost-optimized setup
export TASK_PLANNER_MODEL="openai:gpt-4o-mini"
export EXECUTOR_MODEL="openai:gpt-4o-mini"
export REFLECTOR_MODEL="openai:gpt-4o"

# All Anthropic
export TASK_PLANNER_MODEL="anthropic:claude-haiku-3-5-20251022"
export EXECUTOR_MODEL="anthropic:claude-sonnet-4-5-20250514"
export REFLECTOR_MODEL="anthropic:claude-sonnet-4-5-20250514"
```

### Running Quality Checks

```bash
# Format code
uv run ruff format .

# Lint
uv run ruff check .

# Type check
uv run basedpyright

# Run tests
uv run pytest

# Run all checks (stops on first failure with clear error)
uv run ruff check . || exit 1
uv run basedpyright || exit 1
uv run pytest || exit 1
```

### Running the Demo

The included toy demo showcases the full orchestration flow:

```bash
# First, set up your configuration
export TASK_PLANNER_MODEL="anthropic:claude-sonnet-4-5-20250514"
export EXECUTOR_MODEL="anthropic:claude-sonnet-4-5-20250514"
export REFLECTOR_MODEL="anthropic:claude-sonnet-4-5-20250514"
export ANTHROPIC_API_KEY="your-api-key-here"

# Run the demo
uv run python examples/toy_demo.py
```

The demo will:
1. Ask for a goal
2. Decompose it into tasks (TaskPlanner)
3. Execute the first 3 tasks (Executor)
4. Reflect on progress and identify gaps (Reflector)
5. Display results and suggestions

### Pre-commit Hooks

Install pre-commit hooks to run quality checks automatically:

```bash
pre-commit install
```

## Project Structure

```
nanoagent/
├── core/              # Core orchestration components
│   ├── task_planner.py
│   ├── executor.py
│   ├── reflector.py
│   └── todo_manager.py
├── models/            # Pydantic data models
│   └── schemas.py
└── tools/             # Tool registry and implementations
```

## Development

This project follows Test-Driven Development (TDD). When implementing features:

1. Write failing test
2. Implement code to pass test
3. Refactor while keeping tests green

Tests live next to source code with `*_test.py` pattern.

## Milestones

**Milestone 1 (Current)**: Foundation with Pydantic AI agents and manual orchestration POC

**Milestone 2**: Automated orchestration loop and pluggable tools

**Milestone 3**: Production hardening and comprehensive documentation
