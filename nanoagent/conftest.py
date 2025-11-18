# ABOUTME: Pytest configuration for nanoagent project
# ABOUTME: Injects TestingSettings and controls LLM test execution

import os

import pytest
from pydantic_ai import models

# Set dummy API keys FIRST, before importing config or agents
# This ensures agents can initialize even without real keys
os.environ.setdefault("ANTHROPIC_API_KEY", "dummy-key-for-testing")
os.environ.setdefault("OPENAI_API_KEY", "dummy-key-for-testing")
os.environ.setdefault("OPENROUTER_API_KEY", "dummy-key-for-testing")

# Now safe to import config - agents will initialize with dummy keys
from nanoagent.config import TestingSettings, set_settings

# Inject test settings with defaults before any agent modules are imported
# This ensures agents use TestingSettings (Anthropic defaults) for tests
set_settings(TestingSettings())

# Explicit flag - user controls when real LLM calls are allowed
# Set ALLOW_MODEL_REQUESTS=true to run tests that make real API calls
ALLOW_REAL_API_CALLS = os.getenv("ALLOW_MODEL_REQUESTS", "").lower() in ("true", "1", "yes")

# Allow API calls only if explicitly enabled
models.ALLOW_MODEL_REQUESTS = ALLOW_REAL_API_CALLS


@pytest.fixture
def require_real_api_key() -> None:
    """Skip test if real LLM calls not enabled via ALLOW_MODEL_REQUESTS."""
    if not ALLOW_REAL_API_CALLS:
        pytest.skip("Set ALLOW_MODEL_REQUESTS=true to run real LLM tests")
