import argparse
import json

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter

from git import Repo

from aider_agent.agent.graph import build_agent_graph
from aider_agent.config import load_settings
from aider_agent.evaluation.cost_latency import (
    summarize_usage,
)
from aider_agent.evaluation.harness import (
    NoOpCandidateApplier,
    StaticApprovalGate,
    load_tasks,
)
from aider_agent.llm.deepseek_client import (
    DeepSeekClient,
)


def create_repository(
    repository_path: Path,
    task: dict,
) -> None:
    """Create one temporary Git repository from a task."""

    repository = task[
        "repository"
    ]

    file_path = repository[
        "file_path"
    ]

    target = (
        repository_path
        / file_path
    )

    target.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    repo = Repo.init(
        repository_path
    )

    try:
        with repo.config_writer() as config:
            config.set_value(
                "user",
                "name",
                "Live Benchmark",
            )

            config.set_value(
                "user",
                "email",
                "benchmark@example.com",
            )

        target.write_text(
            repository[
                "initial_content"
            ],
            encoding="utf-8",
        )

        repo.index.add(
            [file_path]
        )

        repo.index.commit(
            "Initial benchmark state"
        )

        target.write_text(
            repository[
                "staged_content"
            ],
            encoding="utf-8",
        )

        repo.index.add(
            [file_path]
        )

    finally:
        repo.close()


def run_task(
    task: dict,
    api_key: str,
    model: str,
) -> dict:
    """Run one controlled task using real DeepSeek."""

    with TemporaryDirectory(
        prefix="aider-live-benchmark-"
    ) as temporary_directory:

        repository_path = Path(
            temporary_directory
        )

        create_repository(
            repository_path,
            task,
        )

        client = DeepSeekClient(
            api_key=api_key,
            model=model,
        )

        # The benchmark never applies generated
        # tests to the temporary repository.
        gate = StaticApprovalGate(
            approved=False
        )

        applier = NoOpCandidateApplier()

        graph = build_agent_graph(
            client,
            approval_gate=gate,
            candidate_applier=applier,
            max_retries=task.get(
                "max_retries",
                3,
            ),
        )

        started_at = perf_counter()

        error = None
        result = {}

        try:
            result = graph.invoke(
                {
                    "repository_path":
                        str(
                            repository_path
                        )
                }
            )

        except Exception as exc:
            error = {
                "type":
                    type(exc).__name__,
                "message":
                    str(exc),
            }

        workflow_latency = (
            perf_counter()
            - started_at
        )

        expected_gap = bool(
            task[
                "expected_test_gap"
            ]
        )

        if error is None:
            detected_gap = bool(
                result.get(
                    "test_gaps",
                    [],
                )
            )
        else:
            detected_gap = None

        usage = summarize_usage(
            client.usage_records
        )

        return {
            "id":
                task["id"],

            "description":
                task.get(
                    "description",
                    "",
                ),

            "expected_test_gap":
                expected_gap,

            "detected_test_gap":
                detected_gap,

            "gap_detection_correct":
                (
                    detected_gap
                    == expected_gap
                    if detected_gap is not None
                    else None
                ),

            "final_status":
                result.get(
                    "status"
                ),

            "test_success":
                result.get(
                    "test_success"
                ),

            "retry_count":
                result.get(
                    "retry_count",
                    0,
                ),

            "workflow_latency_seconds":
                workflow_latency,

            "usage":
                usage,

            "failed_api_request_count":
                len(
                    client.failed_request_records
                ),

            "error":
                error,
        }


def calculate_semantic_metrics(
    results: list[dict],
) -> dict:
    """Calculate simple live gap-detection metrics."""

    completed = [
        result
        for result
        in results
        if result["error"] is None
    ]

    positive = [
        result
        for result
        in completed
        if result[
            "expected_test_gap"
        ]
    ]

    negative = [
        result
        for result
        in completed
        if not result[
            "expected_test_gap"
        ]
    ]

    true_positives = sum(
        1
        for result
        in positive
        if result[
            "detected_test_gap"
        ]
    )

    false_positives = sum(
        1
        for result
        in negative
        if result[
            "detected_test_gap"
        ]
    )

    detection_rate = (
        true_positives
        / len(positive)
        if positive
        else None
    )

    false_positive_rate = (
        false_positives
        / len(negative)
        if negative
        else None
    )

    return {
        "completed_task_count":
            len(completed),

        "benchmark_error_count":
            len(results)
            - len(completed),

        "test_gap_detection_rate":
            detection_rate,

        "false_positive_rate":
            false_positive_rate,
    }


def combine_usage(
    results: list[dict],
) -> dict:
    """Combine usage across all benchmark tasks."""

    total_calls = sum(
        result[
            "usage"
        ][
            "llm_call_count"
        ]
        for result
        in results
    )

    token_names = [
        "prompt",
        "prompt_cache_hit",
        "prompt_cache_miss",
        "completion",
        "reasoning",
        "total",
    ]

    tokens = {
        name: sum(
            result[
                "usage"
            ][
                "tokens"
            ][
                name
            ]
            for result
            in results
        )
        for name
        in token_names
    }

    llm_latency = sum(
        result[
            "usage"
        ][
            "latency_seconds"
        ][
            "total"
        ]
        for result
        in results
    )

    workflow_latency = sum(
        result[
            "workflow_latency_seconds"
        ]
        for result
        in results
    )

    off_peak_cost = sum(
        result[
            "usage"
        ][
            "estimated_cost_usd"
        ][
            "off_peak"
        ]
        for result
        in results
    )

    peak_cost = sum(
        result[
            "usage"
        ][
            "estimated_cost_usd"
        ][
            "peak"
        ]
        for result
        in results
    )

    task_count = len(
        results
    )

    return {
        "llm_call_count":
            total_calls,

        "tokens":
            tokens,

        "llm_latency_seconds": {
            "total":
                llm_latency,
            "average_per_call":
                (
                    llm_latency
                    / total_calls
                    if total_calls
                    else 0.0
                ),
        },

        "workflow_latency_seconds": {
            "total":
                workflow_latency,
            "average_per_task":
                (
                    workflow_latency
                    / task_count
                    if task_count
                    else 0.0
                ),
        },

        "estimated_cost_usd": {
            "off_peak":
                off_peak_cost,
            "peak":
                peak_cost,
        },
    }


def format_percentage(
    value: float | None,
) -> str:
    """Format an optional percentage."""

    if value is None:
        return "N/A"

    return (
        f"{value * 100:.1f}%"
    )


def main():
    """Run the live DeepSeek benchmark."""

    parser = argparse.ArgumentParser(
        description=(
            "Run controlled tasks using "
            "the real DeepSeek API."
        )
    )

    parser.add_argument(
        "--tasks",
        default=(
            "evaluation/tasks.json"
        ),
    )

    parser.add_argument(
        "--output",
        default=(
            "evaluation/results/"
            "live_latest.json"
        ),
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help=(
            "Run only the first N tasks."
        ),
    )

    args = parser.parse_args()

    settings = load_settings()

    api_key = (
        settings
        .require_deepseek_api_key()
    )

    tasks = load_tasks(
        args.tasks
    )

    if args.limit is not None:
        if args.limit <= 0:
            raise ValueError(
                "--limit must be greater than zero."
            )

        tasks = tasks[
            :args.limit
        ]

    results = []

    print()
    print(
        "=== Aider Live DeepSeek Benchmark ==="
    )

    print(
        "Model:",
        settings.llm_model,
    )

    print(
        "Tasks:",
        len(tasks),
    )

    print()

    for index, task in enumerate(
        tasks,
        start=1,
    ):
        print(
            f"[{index}/{len(tasks)}] "
            f"{task['id']}..."
        )

        result = run_task(
            task=task,
            api_key=api_key,
            model=settings.llm_model,
        )

        results.append(
            result
        )

        print(
            "  Status:",
            result["final_status"],
        )

        print(
            "  LLM calls:",
            result[
                "usage"
            ][
                "llm_call_count"
            ],
        )

        print(
            "  Workflow seconds:",
            (
                f"{result['workflow_latency_seconds']:.2f}"
            ),
        )

        if result[
            "error"
        ] is not None:
            print(
                "  ERROR:",
                result[
                    "error"
                ][
                    "message"
                ],
            )

    semantic_metrics = (
        calculate_semantic_metrics(
            results
        )
    )

    totals = combine_usage(
        results
    )

    report = {
        "evaluation_mode":
            "live_deepseek",

        "generated_at_utc":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "model":
            settings.llm_model,

        "task_count":
            len(results),

        "semantic_metrics":
            semantic_metrics,

        "cost_latency":
            totals,

        "pricing_note": (
            "Cost values are estimates based on "
            "reported token usage and the dated "
            "DeepSeek pricing snapshot. They are "
            "not a billing invoice."
        ),

        "tasks":
            results,
    }

    output_path = Path(
        args.output
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print()
    print(
        "=== Live Benchmark Summary ==="
    )

    print(
        "Completed tasks:",
        semantic_metrics[
            "completed_task_count"
        ],
    )

    print(
        "Benchmark errors:",
        semantic_metrics[
            "benchmark_error_count"
        ],
    )

    print(
        "Test-gap detection rate:",
        format_percentage(
            semantic_metrics[
                "test_gap_detection_rate"
            ]
        ),
    )

    print(
        "False-positive rate:",
        format_percentage(
            semantic_metrics[
                "false_positive_rate"
            ]
        ),
    )

    print(
        "LLM calls:",
        totals[
            "llm_call_count"
        ],
    )

    print(
        "Prompt tokens:",
        totals[
            "tokens"
        ][
            "prompt"
        ],
    )

    print(
        "Cache-hit prompt tokens:",
        totals[
            "tokens"
        ][
            "prompt_cache_hit"
        ],
    )

    print(
        "Cache-miss prompt tokens:",
        totals[
            "tokens"
        ][
            "prompt_cache_miss"
        ],
    )

    print(
        "Output tokens:",
        totals[
            "tokens"
        ][
            "completion"
        ],
    )

    print(
        "Total tokens:",
        totals[
            "tokens"
        ][
            "total"
        ],
    )

    print(
        "Total LLM latency:",
        (
            f"{totals['llm_latency_seconds']['total']:.2f}s"
        ),
    )

    print(
        "Average LLM-call latency:",
        (
            f"{totals['llm_latency_seconds']['average_per_call']:.2f}s"
        ),
    )

    print(
        "Total workflow latency:",
        (
            f"{totals['workflow_latency_seconds']['total']:.2f}s"
        ),
    )

    print(
        "Average workflow latency:",
        (
            f"{totals['workflow_latency_seconds']['average_per_task']:.2f}s"
        ),
    )

    print(
        "Estimated off-peak cost:",
        (
            "$"
            f"{totals['estimated_cost_usd']['off_peak']:.6f}"
        ),
    )

    print(
        "Estimated peak cost:",
        (
            "$"
            f"{totals['estimated_cost_usd']['peak']:.6f}"
        ),
    )

    print(
        "Report:",
        output_path.as_posix(),
    )


if __name__ == "__main__":
    main()