import pytest

from aider_agent.config import Settings


def test_settings_returns_api_key():
    """Settings should return a configured DeepSeek API key."""

    settings = Settings(
        llm_provider="deepseek",
        llm_model="deepseek-flash",
        deepseek_api_key="test-key",
    )

    assert settings.require_deepseek_api_key() == "test-key"


def test_settings_rejects_missing_api_key():
    """Settings should reject a missing DeepSeek API key."""

    settings = Settings(
        llm_provider="deepseek",
        llm_model="deepseek-flash",
        deepseek_api_key=None,
    )

    with pytest.raises(
        ValueError,
        match="DEEPSEEK_API_KEY is missing",
    ):
        settings.require_deepseek_api_key()


def test_settings_rejects_example_api_key():
    """The placeholder API key must not be accepted."""

    settings = Settings(
        llm_provider="deepseek",
        llm_model="deepseek-flash",
        deepseek_api_key="your_api_key_here",
    )

    with pytest.raises(
        ValueError,
        match="DEEPSEEK_API_KEY is missing",
    ):
        settings.require_deepseek_api_key()