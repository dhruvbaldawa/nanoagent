# ABOUTME: Pytest configuration for nanoagent project
# ABOUTME: Sets up safety guards and shared fixtures for all tests

import os

import pytest
from pydantic_ai import models

# Check if a REAL API key exists BEFORE setting any dummy key
# Export this so test modules can check it in their skipif decorators
HAS_REAL_API_KEY = bool(os.getenv("ANTHROPIC_API_KEY"))

# Set dummy API key if not available - allows agent initialization without crashing
# Agents need an API key to initialize, even if they'll use TestModel in tests
if not HAS_REAL_API_KEY:
    os.environ["ANTHROPIC_API_KEY"] = "dummy-key-for-testing"

# Allow API calls only if a real API key was provided
# Tests that need real API calls will be skipped via require_real_api_key fixture
# Tests that use TestModel.override() work regardless of ALLOW_MODEL_REQUESTS
models.ALLOW_MODEL_REQUESTS = HAS_REAL_API_KEY


@pytest.fixture
def require_real_api_key() -> None:
    """Skip test if no real ANTHROPIC_API_KEY is available (for real LLM tests)."""
    if not HAS_REAL_API_KEY:
        pytest.skip("ANTHROPIC_API_KEY not set (required for real LLM calls)")
