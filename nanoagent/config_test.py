# ABOUTME: Tests for configuration module with per-agent model settings
# ABOUTME: Validates Settings (strict), TestingSettings (permissive), and global management

import pytest
from pydantic import ValidationError

from nanoagent.config import Settings, TestingSettings, get_settings, set_settings


class TestProductionSettings:
    """Test strict production Settings - requires explicit configuration."""

    def test_requires_all_models(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Production Settings fails if any model env var missing."""
        monkeypatch.delenv("TASK_PLANNER_MODEL", raising=False)
        monkeypatch.delenv("EXECUTOR_MODEL", raising=False)
        monkeypatch.delenv("REFLECTOR_MODEL", raising=False)

        with pytest.raises(ValidationError) as exc_info:
            Settings()  # type: ignore[call-arg]

        # Should show which fields are missing
        error_str = str(exc_info.value)
        assert "task_planner_model" in error_str
        assert "executor_model" in error_str
        assert "reflector_model" in error_str

    def test_validates_model_format(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Model must be 'provider:model' format."""
        monkeypatch.setenv("TASK_PLANNER_MODEL", "invalid-format")
        monkeypatch.setenv("EXECUTOR_MODEL", "openai:gpt-4o")
        monkeypatch.setenv("REFLECTOR_MODEL", "openai:gpt-4o")

        with pytest.raises(ValidationError, match="provider:model-name"):
            Settings()  # type: ignore[call-arg]

    def test_multiple_invalid_models(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Multiple invalid models should show all errors."""
        monkeypatch.setenv("TASK_PLANNER_MODEL", "bad1")
        monkeypatch.setenv("EXECUTOR_MODEL", "bad2")
        monkeypatch.setenv("REFLECTOR_MODEL", "bad3")

        with pytest.raises(ValidationError) as exc_info:
            Settings()  # type: ignore[call-arg]

        error_str = str(exc_info.value)
        assert "bad1" in error_str or "provider:model-name" in error_str

    def test_valid_models_creates_settings(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Valid model format creates Settings successfully."""
        monkeypatch.setenv("TASK_PLANNER_MODEL", "openai:gpt-4o")
        monkeypatch.setenv("EXECUTOR_MODEL", "anthropic:claude-sonnet-4-5-20250514")
        monkeypatch.setenv("REFLECTOR_MODEL", "openrouter:meta-llama/llama-3.1-70b")

        settings = Settings()  # type: ignore[call-arg]
        assert settings.task_planner_model == "openai:gpt-4o"
        assert settings.executor_model == "anthropic:claude-sonnet-4-5-20250514"
        assert settings.reflector_model == "openrouter:meta-llama/llama-3.1-70b"

    def test_reads_api_keys(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Settings reads API keys from environment."""
        monkeypatch.setenv("TASK_PLANNER_MODEL", "openai:gpt-4o")
        monkeypatch.setenv("EXECUTOR_MODEL", "openai:gpt-4o")
        monkeypatch.setenv("REFLECTOR_MODEL", "openai:gpt-4o")
        monkeypatch.setenv("OPENAI_API_KEY", "test-key-openai-123")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-anthropic-456")
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-openrouter-789")

        settings = Settings()  # type: ignore[call-arg]
        assert settings.openai_api_key == "test-key-openai-123"
        assert settings.anthropic_api_key == "test-key-anthropic-456"
        assert settings.openrouter_api_key == "test-key-openrouter-789"

    def test_api_keys_optional(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """API keys are optional - Settings works without them."""
        monkeypatch.setenv("TASK_PLANNER_MODEL", "openai:gpt-4o")
        monkeypatch.setenv("EXECUTOR_MODEL", "openai:gpt-4o")
        monkeypatch.setenv("REFLECTOR_MODEL", "openai:gpt-4o")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

        settings = Settings()  # type: ignore[call-arg]  # Should not raise
        assert settings.openai_api_key is None
        assert settings.anthropic_api_key is None
        assert settings.openrouter_api_key is None

    def test_get_model_instance_without_explicit_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Without explicit key, return model string for Pydantic AI."""
        monkeypatch.setenv("TASK_PLANNER_MODEL", "openai:gpt-4o")
        monkeypatch.setenv("EXECUTOR_MODEL", "openai:gpt-4o")
        monkeypatch.setenv("REFLECTOR_MODEL", "openai:gpt-4o")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        settings = Settings()  # type: ignore[call-arg]
        model = settings.get_model_instance("openai:gpt-4o")
        assert isinstance(model, str)
        assert model == "openai:gpt-4o"

    def test_get_model_instance_returns_string(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """get_model_instance returns model string for Pydantic AI to handle."""
        monkeypatch.setenv("TASK_PLANNER_MODEL", "openai:gpt-4o")
        monkeypatch.setenv("EXECUTOR_MODEL", "openai:gpt-4o")
        monkeypatch.setenv("REFLECTOR_MODEL", "openai:gpt-4o")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

        settings = Settings()  # type: ignore[call-arg]
        model = settings.get_model_instance("openai:gpt-4o")

        # Currently returns string - Pydantic AI handles API key detection
        assert isinstance(model, str)
        assert model == "openai:gpt-4o"

    def test_different_providers_same_settings(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Can use different providers in same Settings instance."""
        monkeypatch.setenv("TASK_PLANNER_MODEL", "openai:gpt-4o")
        monkeypatch.setenv("EXECUTOR_MODEL", "anthropic:claude-sonnet-4-5-20250514")
        monkeypatch.setenv("REFLECTOR_MODEL", "openrouter:meta-llama/llama-3.1-70b")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-openai")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-anthropic")
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-openrouter")

        settings = Settings()  # type: ignore[call-arg]
        assert settings.task_planner_model.startswith("openai:")
        assert settings.executor_model.startswith("anthropic:")
        assert settings.reflector_model.startswith("openrouter:")


class TestTestingSettings:
    """Test permissive TestingSettings - provides sensible defaults."""

    def test_has_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """TestingSettings works without env vars."""
        monkeypatch.delenv("TASK_PLANNER_MODEL", raising=False)
        monkeypatch.delenv("EXECUTOR_MODEL", raising=False)
        monkeypatch.delenv("REFLECTOR_MODEL", raising=False)

        settings = TestingSettings()  # Should not raise
        assert settings.task_planner_model == "anthropic:claude-sonnet-4-5-20250514"
        assert settings.executor_model == "anthropic:claude-sonnet-4-5-20250514"
        assert settings.reflector_model == "anthropic:claude-sonnet-4-5-20250514"

    def test_env_overrides_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Env vars can override TestingSettings defaults."""
        monkeypatch.setenv("TASK_PLANNER_MODEL", "openai:gpt-4o-mini")
        monkeypatch.delenv("EXECUTOR_MODEL", raising=False)
        monkeypatch.delenv("REFLECTOR_MODEL", raising=False)

        settings = TestingSettings()
        assert settings.task_planner_model == "openai:gpt-4o-mini"
        # Others still use defaults
        assert settings.executor_model == "anthropic:claude-sonnet-4-5-20250514"
        assert settings.reflector_model == "anthropic:claude-sonnet-4-5-20250514"

    def test_partial_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Can override specific agents while others keep defaults."""
        monkeypatch.setenv("EXECUTOR_MODEL", "openai:gpt-4o")
        monkeypatch.delenv("TASK_PLANNER_MODEL", raising=False)
        monkeypatch.delenv("REFLECTOR_MODEL", raising=False)

        settings = TestingSettings()
        assert settings.task_planner_model == "anthropic:claude-sonnet-4-5-20250514"  # Default
        assert settings.executor_model == "openai:gpt-4o"  # Override
        assert settings.reflector_model == "anthropic:claude-sonnet-4-5-20250514"  # Default

    def test_api_keys_optional(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """TestingSettings works without API keys."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

        settings = TestingSettings()
        assert settings.openai_api_key is None
        assert settings.anthropic_api_key is None
        assert settings.openrouter_api_key is None


class TestSettingsGlobalManagement:
    """Test global settings instance management."""

    def test_get_settings_singleton(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """get_settings() returns same instance on repeated calls."""
        monkeypatch.setenv("TASK_PLANNER_MODEL", "openai:gpt-4o")
        monkeypatch.setenv("EXECUTOR_MODEL", "openai:gpt-4o")
        monkeypatch.setenv("REFLECTOR_MODEL", "openai:gpt-4o")

        # Reset global state
        import nanoagent.config

        nanoagent.config._settings = None  # type: ignore[assignment]

        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2

    def test_set_settings_overrides_global(self) -> None:
        """set_settings() allows test override of global instance."""
        test_settings = TestingSettings()
        set_settings(test_settings)

        retrieved = get_settings()
        assert retrieved is test_settings
        assert isinstance(retrieved, TestingSettings)

    def test_set_and_get_different_types(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Can set TestingSettings and retrieve it as Settings base class."""
        test_settings = TestingSettings()
        set_settings(test_settings)

        retrieved = get_settings()
        assert isinstance(retrieved, Settings)
        assert isinstance(retrieved, TestingSettings)

    def test_settings_used_immediately(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Changed settings are immediately available via get_settings()."""
        test_settings_1 = TestingSettings()
        set_settings(test_settings_1)
        assert get_settings() is test_settings_1

        monkeypatch.setenv("EXECUTOR_MODEL", "openai:gpt-4o")
        test_settings_2 = TestingSettings()
        set_settings(test_settings_2)
        assert get_settings() is test_settings_2
        assert get_settings().executor_model == "openai:gpt-4o"
