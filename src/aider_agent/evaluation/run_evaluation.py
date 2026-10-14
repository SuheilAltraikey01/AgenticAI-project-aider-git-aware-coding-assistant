import argparse
import json

from pathlib import Path

from aider_agent.evaluation.harness import (
    EvaluationHarness,
    load_tasks,
)


def percentage(
    value: float,
) -> str:
    """Format a ratio as a percentage."""

    return f"{value * 100:.1f}%"


def main():
    """Run the deterministic offline evaluation suite."""

    parser = argparse.ArgumentParser(
        description=(
            "Run the Aider agent controlled "
            "offline evaluation suite."
        )
    )

    parser.add_argument(
        "--tasks",
        default="evaluation/tasks.json",
        help=(
            "Path to the controlled evaluation "
            "task JSON file."
        ),
    )

    parser.add_argument(
        "--output",
        default=(
            "evaluation/results/latest.json"
        ),
        help=(
            "Path for the generated JSON "
            "evaluation report."
        ),
    )

    args = parser.parse_args()

    tasks = load_tasks(
        args.tasks
    )

    harness = EvaluationHarness(
        tasks
    )

    report = harness.run()

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

    metrics = report[
        "metrics"
    ]

    print()
    print(
        "=== Aider Offline Evaluation ==="
    )

    print(
        "Tasks:",
        report["task_count"],
    )

    print(
        "Test-gap detection rate:",
        percentage(
            metrics[
                "test_gap_detection_rate"
            ]
        ),
    )

    print(
        "False-positive rate:",
        percentage(
            metrics[
                "false_positive_rate"
            ]
        ),
    )

    print(
        "Candidate quality proxy:",
        percentage(
            metrics[
                "candidate_quality_proxy_rate"
            ]
        ),
    )

    print(
        "Convergence rate:",
        percentage(
            metrics[
                "convergence_rate"
            ]
        ),
    )

    print(
        "Final-status accuracy:",
        percentage(
            metrics[
                "final_status_accuracy"
            ]
        ),
    )

    print(
        "Average retry count:",
        f"{metrics['average_retry_count']:.2f}",
    )

    print(
        "Average retries to convergence:",
        (
            f"{metrics['average_retries_to_convergence']:.2f}"
        ),
    )

    print(
        "Retry-limit cases:",
        metrics[
            "retry_limit_count"
        ],
    )

    print(
        "Report:",
        output_path.as_posix(),
    )


if __name__ == "__main__":
    main()