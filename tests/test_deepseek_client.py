import pytest

from aider_agent.llm.deepseek_client import DeepSeekClient


def test_deepseek_client_rejects_empty_api_key():
    """The client should reject an empty API key."""

    with pytest.raises(
        ValueError,
        match="DeepSeek API key cannot be empty",
    ):
        DeepSeekClient(
            api_key="",
            model="deepseek-flash",
        )


def test_deepseek_client_keeps_configured_model():
    """The client should keep the configured model name."""

    client = DeepSeekClient(
        api_key="test-key",
        model="deepseek-flash",
    )

    assert client.model == "deepseek-flash"