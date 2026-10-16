import pytest

from aider_agent.evaluation.cost_latency import (
    summarize_usage,
)


def test_usage_summary_calculates_tokens_latency_and_cost():
    """Usage records should produce reproducible cost estimates."""

    records = [
        {
            "model":
                "deepseek-flash",
            "latency_seconds":
                2.0,
            "prompt_tokens":
                2_000_000,
            "prompt_cache_hit_tokens":
                1_000_000,
            "prompt_cache_miss_tokens":
                1_000_000,
            "completion_tokens":
                1_000_000,
            "reasoning_tokens":
                0,
            "total_tokens":
                3_000_000,
        }
    ]

    summary = summarize_usage(
        records
    )

    assert (
        summary["llm_call_count"]
        == 1
    )

    assert (
        summary["tokens"]["prompt"]
        == 2_000_000
    )

    assert (
        summary[
            "tokens"
        ][
            "prompt_cache_hit"
        ]
        == 1_000_000
    )

    assert (
        summary[
            "tokens"
        ][
            "prompt_cache_miss"
        ]
        == 1_000_000
    )

    assert (
        summary[
            "tokens"
        ][
            "completion"
        ]
        == 1_000_000
    )

    assert (
        summary[
            "latency_seconds"
        ][
            "average"
        ]
        == pytest.approx(
            2.0
        )
    )

    # 1M hit * $0.003
    # + 1M miss * $0.15
    # + 1M output * $0.60
    assert (
        summary[
            "estimated_cost_usd"
        ][
            "off_peak"
        ]
        == pytest.approx(
            0.753
        )
    )

    assert (
        summary[
            "estimated_cost_usd"
        ][
            "peak"
        ]
        == pytest.approx(
            1.506
        )
    )


def test_empty_usage_summary_returns_zero_values():
    """Empty usage should produce zero metrics."""

    summary = summarize_usage(
        []
    )

    assert (
        summary["llm_call_count"]
        == 0
    )

    assert (
        summary[
            "tokens"
        ][
            "total"
        ]
        == 0
    )

    assert (
        summary[
            "latency_seconds"
        ][
            "total"
        ]
        == 0.0
    )

    assert (
        summary[
            "estimated_cost_usd"
        ][
            "off_peak"
        ]
        == 0.0
    )

    assert (
        summary[
            "estimated_cost_usd"
        ][
            "peak"
        ]
        == 0.0
    )