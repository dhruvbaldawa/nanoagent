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

### Installation

```bash
uv sync
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
