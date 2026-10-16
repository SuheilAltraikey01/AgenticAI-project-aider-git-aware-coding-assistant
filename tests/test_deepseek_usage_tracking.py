from types import SimpleNamespace

from aider_agent.llm.deepseek_client import (
    DeepSeekClient,
)


class FakeCompletions:
    """Return a fake DeepSeek-compatible response."""

    def create(
        self,
        **kwargs,
    ):
        return SimpleNamespace(
            model="deepseek-flash",
            usage=SimpleNamespace(
                prompt_tokens=120,
                prompt_cache_hit_tokens=20,
                prompt_cache_miss_tokens=100,
                completion_tokens=30,
                total_tokens=150,
                completion_tokens_details=(
                    SimpleNamespace(
                        reasoning_tokens=0
                    )
                ),
            ),
            choices=[
                SimpleNamespace(
                    finish_reason="stop",
                    message=SimpleNamespace(
                        content='{"result":"ok"}'
                    ),
                )
            ],
        )


def test_deepseek_client_records_usage_without_network():
    """Usage tracking should work without making a network call."""

    client = DeepSeekClient(
        api_key="dummy-test-key",
        model="deepseek-flash",
    )

    client._client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=FakeCompletions()
        )
    )

    response = client.generate(
        system_prompt="System",
        user_prompt="User",
    )

    assert (
        response
        == '{"result":"ok"}'
    )

    assert len(
        client.usage_records
    ) == 1

    usage = (
        client.usage_records[0]
    )

    assert (
        usage["prompt_tokens"]
        == 120
    )

    assert (
        usage[
            "prompt_cache_hit_tokens"
        ]
        == 20
    )

    assert (
        usage[
            "prompt_cache_miss_tokens"
        ]
        == 100
    )

    assert (
        usage["completion_tokens"]
        == 30
    )

    assert (
        usage["total_tokens"]
        == 150
    )

    assert (
        usage["latency_seconds"]
        >= 0
    )