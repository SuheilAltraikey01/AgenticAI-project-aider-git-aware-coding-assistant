from pathlib import Path

from aider_agent.evaluation.harness import (
    EvaluationHarness,
    load_tasks,
)


TASKS_PATH = Path(
    "evaluation/tasks.json"
)


def test_controlled_task_set_has_at_least_five_tasks():
    """The academic evaluation set should contain several scenarios."""

    tasks = load_tasks(
        TASKS_PATH
    )

    assert len(
        tasks
    ) >= 5


def test_offline_evaluation_is_deterministic():
    """The controlled offline task set should reproduce expected results."""

    tasks = load_tasks(
        TASKS_PATH
    )

    harness = EvaluationHarness(
        tasks
    )

    report = harness.run()

    assert (
        report["evaluation_mode"]
        == "offline_deterministic"
    )

    assert (
        report["task_count"]
        == len(tasks)
    )

    metrics = report[
        "metrics"
    ]

    assert (
        metrics[
            "test_gap_detection_rate"
        ]
        == 1.0
    )

    assert (
        metrics[
            "false_positive_rate"
        ]
        == 0.0
    )

    assert (
        metrics[
            "candidate_quality_proxy_rate"
        ]
        == 1.0
    )

    assert (
        metrics[
            "final_status_accuracy"
        ]
        == 1.0
    )


def test_evaluation_includes_retry_limit_case():
    """The controlled suite should exercise bounded termination."""

    tasks = load_tasks(
        TASKS_PATH
    )

    harness = EvaluationHarness(
        tasks
    )

    report = harness.run()

    assert (
        report["metrics"][
            "retry_limit_count"
        ]
        >= 1
    )

    statuses = {
        task[
            "actual_final_status"
        ]
        for task
        in report[
            "tasks"
        ]
    }

    assert (
        "retry_limit_reached"
        in statuses
    )

    assert (
        "approval_rejected"
        in statuses
    )

    assert (
        "approved_tests_applied"
        in statuses
    )
    