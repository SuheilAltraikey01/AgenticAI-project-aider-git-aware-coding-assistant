from statistics import mean


PRICING_SNAPSHOT_DATE = "2026-10-16"

PRICING_SOURCE = (
    "https://api-docs.deepseek.com/quick_start/pricing/"
)


DEEPSEEK_FLASH_PRICING_USD_PER_MILLION = {
    "off_peak": {
        "input_cache_hit": 0.003,
        "input_cache_miss": 0.15,
        "output": 0.60,
    },
    "peak": {
        "input_cache_hit": 0.006,
        "input_cache_miss": 0.30,
        "output": 1.20,
    },
}


def _estimate_cost(
    cache_hit_tokens: int,
    cache_miss_tokens: int,
    output_tokens: int,
    tier: str,
) -> float:
    """Estimate API cost for one pricing tier."""

    prices = (
        DEEPSEEK_FLASH_PRICING_USD_PER_MILLION[
            tier
        ]
    )

    cache_hit_cost = (
        cache_hit_tokens
        / 1_000_000
        * prices[
            "input_cache_hit"
        ]
    )

    cache_miss_cost = (
        cache_miss_tokens
        / 1_000_000
        * prices[
            "input_cache_miss"
        ]
    )

    output_cost = (
        output_tokens
        / 1_000_000
        * prices[
            "output"
        ]
    )

    return (
        cache_hit_cost
        + cache_miss_cost
        + output_cost
    )


def summarize_usage(
    usage_records: list[dict],
) -> dict:
    """Summarize token usage, latency, and estimated cost."""

    latencies = [
        float(
            record.get(
                "latency_seconds",
                0.0,
            )
        )
        for record
        in usage_records
    ]

    prompt_tokens = sum(
        int(
            record.get(
                "prompt_tokens",
                0,
            )
        )
        for record
        in usage_records
    )

    cache_hit_tokens = sum(
        int(
            record.get(
                "prompt_cache_hit_tokens",
                0,
            )
        )
        for record
        in usage_records
    )

    cache_miss_tokens = sum(
        int(
            record.get(
                "prompt_cache_miss_tokens",
                0,
            )
        )
        for record
        in usage_records
    )

    completion_tokens = sum(
        int(
            record.get(
                "completion_tokens",
                0,
            )
        )
        for record
        in usage_records
    )

    reasoning_tokens = sum(
        int(
            record.get(
                "reasoning_tokens",
                0,
            )
        )
        for record
        in usage_records
    )

    total_tokens = sum(
        int(
            record.get(
                "total_tokens",
                0,
            )
        )
        for record
        in usage_records
    )

    off_peak_cost = _estimate_cost(
        cache_hit_tokens=
            cache_hit_tokens,
        cache_miss_tokens=
            cache_miss_tokens,
        output_tokens=
            completion_tokens,
        tier="off_peak",
    )

    peak_cost = _estimate_cost(
        cache_hit_tokens=
            cache_hit_tokens,
        cache_miss_tokens=
            cache_miss_tokens,
        output_tokens=
            completion_tokens,
        tier="peak",
    )

    if latencies:
        latency_total = sum(
            latencies
        )

        latency_average = mean(
            latencies
        )

        latency_minimum = min(
            latencies
        )

        latency_maximum = max(
            latencies
        )

    else:
        latency_total = 0.0
        latency_average = 0.0
        latency_minimum = 0.0
        latency_maximum = 0.0

    return {
        "pricing_snapshot_date":
            PRICING_SNAPSHOT_DATE,

        "pricing_source":
            PRICING_SOURCE,

        "llm_call_count":
            len(
                usage_records
            ),

        "tokens": {
            "prompt":
                prompt_tokens,
            "prompt_cache_hit":
                cache_hit_tokens,
            "prompt_cache_miss":
                cache_miss_tokens,
            "completion":
                completion_tokens,
            "reasoning":
                reasoning_tokens,
            "total":
                total_tokens,
        },

        "latency_seconds": {
            "total":
                latency_total,
            "average":
                latency_average,
            "minimum":
                latency_minimum,
            "maximum":
                latency_maximum,
        },

        "estimated_cost_usd": {
            "off_peak":
                off_peak_cost,
            "peak":
                peak_cost,
        },
    }
