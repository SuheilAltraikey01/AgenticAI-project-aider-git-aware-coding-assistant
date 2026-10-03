import pytest

from aider_agent.llm.fake_client import FakeLlmClient


def test_fake_client_returns_configured_response():
    """The fake client should return its predefined response."""

    client = FakeLlmClient(
        responses=[
            "FAKE_RESPONSE"
        ]
    )

    result = client.generate(
        system_prompt="System prompt",
        user_prompt="User prompt",
    )

    assert result == "FAKE_RESPONSE"


def test_fake_client_returns_responses_in_order():
    """Multiple responses should be returned in configured order."""

    client = FakeLlmClient(
        responses=[
            "FIRST",
            "SECOND",
        ]
    )

    first = client.generate(
        system_prompt="System",
        user_prompt="First request",
    )

    second = client.generate(
        system_prompt="System",
        user_prompt="Second request",
    )

    assert first == "FIRST"
    assert second == "SECOND"


def test_fake_client_records_calls():
    """The fake client should record prompts for later inspection."""

    client = FakeLlmClient(
        responses=[
            "OK"
        ]
    )

    client.generate(
        system_prompt="You are a coding assistant.",
        user_prompt="Review this staged diff.",
        max_tokens=500,
    )

    assert len(client.calls) == 1

    assert (
        client.calls[0]["system_prompt"]
        == "You are a coding assistant."
    )

    assert (
        client.calls[0]["user_prompt"]
        == "Review this staged diff."
    )

    assert client.calls[0]["max_tokens"] == 500


def test_fake_client_fails_when_responses_are_exhausted():
    """The fake client should fail clearly when no responses remain."""

    client = FakeLlmClient(
        responses=[]
    )

    with pytest.raises(
        RuntimeError,
        match="no configured responses remaining",
    ):
        client.generate(
            system_prompt="System",
            user_prompt="User",
        )