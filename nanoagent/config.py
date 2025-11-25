# ABOUTME: Configuration module for per-agent LLM model selection
# ABOUTME: Supports production (strict) and test (permissive) settings with explicit API key passing
import os
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Production settings - requires explicit model configuration for each agent."""

    task_planner_model: str = Field(..., description="Model for TaskPlanner agent (e.g., 'openai:gpt-4o')")
    executor_model: str = Field(
        ..., description="Model for Executor agent (e.g., 'openrouter:anthropic/claude-3.5-sonnet')"
    )
    reflector_model: str = Field(
        ..., description="Model for Reflector agent (e.g., 'anthropic:claude-sonnet-4-5-20250514')"
    )

    # Optional API keys - can be passed explicitly to models instead of relying on env var auto-detection
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    openrouter_api_key: str | None = None

    @field_validator("task_planner_model", "executor_model", "reflector_model")
    @classmethod
    def validate_model_format(cls, v: str) -> str:
        """Validate model is in 'provider:model-name' format."""
        if ":" not in v:
            raise ValueError(f"Model '{v}' must be in format 'provider:model-name' (e.g., 'openai:gpt-4o')")
        return v

    def get_model_instance(self, model_str: str) -> str:
        """
        Get model instance or string for agent initialization.

        For now, returns the model string and lets Pydantic AI read API keys from environment.
        In future, can be extended to create explicit model instances when needed.

        Args:
            model_str: Model identifier in format 'provider:model-name'

        Returns:
            Model string for Pydantic AI to initialize
        """
        # Currently returns string - Pydantic AI handles env var reading
        # Future: Can create explicit model instances with api_key passed in
        return model_str

    model_config = SettingsConfigDict(
        env_file=Path(os.getcwd()) / ".env", env_prefix=""
    )  # Read exact environment variable names


class ProductionSettings(Settings):
    """Alias for Settings to make intent clear in production code."""

    pass


class TestingSettings(Settings):
    """Test settings - provides sensible defaults for test environments."""

    task_planner_model: str = "openrouter:minimax/minimax-m2"
    executor_model: str = "openrouter:minimax/minimax-m2"
    reflector_model: str = "openrouter:minimax/minimax-m2"

    model_config = SettingsConfigDict(env_file=None, env_prefix="")


# Global settings instance - can be overridden via set_settings()
_settings: Settings | None = None


def get_settings() -> Settings:
    """
    Get the current global Settings instance.

    Initializes with production Settings (strict) on first call if not overridden.
    Tests can override with TestSettings via set_settings().

    Returns:
        Current Settings instance (TestSettings in tests, Settings in production)

    Raises:
        ValidationError: If production Settings requires env vars that aren't set
    """
    global _settings
    if _settings is None:
        _settings = Settings()  # type: ignore[call-arg]
    return _settings


def set_settings(settings: Settings) -> None:
    """
    Override the global Settings instance (used for testing).

    Args:
        settings: Settings instance to use globally (typically TestSettings with defaults)
    """
    global _settings
    _settings = settings
