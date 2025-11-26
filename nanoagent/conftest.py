# ABOUTME: Pytest configuration for nanoagent project
# ABOUTME: Injects TestingSettings and controls LLM test execution

import os
from collections.abc import Callable
from typing import TYPE_CHECKING

import pytest
from pydantic_ai import models

if TYPE_CHECKING:
    from nanoagent.config import Settings

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
    """Skip the test if real LLM calls not enabled via ALLOW_MODEL_REQUESTS."""
    if not ALLOW_REAL_API_CALLS:
        pytest.skip("Set ALLOW_MODEL_REQUESTS=true to run real LLM tests")


@pytest.fixture
def make_settings(monkeypatch: pytest.MonkeyPatch) -> Callable[..., "Settings"]:
    """Factory fixture for creating Settings instances with custom env vars.

    Args:
        read_env_file: If False (default), isolates from .env file. If True, reads from .env.
        **env_vars: Environment variables to set/unset (None value means delete the env var)

    Returns:
        Callable that creates a Settings instance configured with specified env vars
    """
    from pydantic_settings import SettingsConfigDict

    from nanoagent.config import Settings

    def _make(read_env_file: bool = False, **env_vars: str | None) -> Settings:
        # Set or delete env vars as specified
        for key, value in env_vars.items():
            if value is None:
                monkeypatch.delenv(key, raising=False)
            else:
                monkeypatch.setenv(key, value)

        if read_env_file:
            # Use normal Settings that reads from .env
            return Settings()  # pyright: ignore[reportCallIssue]

        # Create an isolated variant that doesn't read .env for cleaner validation testing
        class IsolatedSettings(Settings):
            model_config = SettingsConfigDict(env_file=None, env_prefix="")

        return IsolatedSettings()  # pyright: ignore[reportCallIssue]

    return _make
