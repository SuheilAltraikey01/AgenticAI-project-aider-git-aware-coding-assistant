from pathlib import Path

from aider_agent.evaluation.run_failure_scenarios import (
    load_failure_scenarios,
    run_failure_suite,
)


SCENARIOS_PATH = Path(
    "evaluation/failure_scenarios.json"
)


def test_failure_scenario_set_contains_required_cases():
    """The suite should cover the main recovery and safety cases."""

    scenarios = load_failure_scenarios(
        SCENARIOS_PATH
    )

    scenario_ids = {
        scenario["id"]
        for scenario
        in scenarios
    }

    required = {
        "timeout_then_recover",
        "retry_limit_reached",
        "no_candidate_generated",
        "human_rejection",
        "malformed_analysis_json",
        "unsafe_candidate_path",
    }

    assert (
        required
        <= scenario_ids
    )


def test_all_failure_scenarios_match_expected_outcomes():
    """Every controlled scenario should behave as designed."""

    scenarios = load_failure_scenarios(
        SCENARIOS_PATH
    )

    report = run_failure_suite(
        scenarios
    )

    assert (
        report[
            "all_expected_outcomes_matched"
        ]
        is True
    )

    assert (
        report[
            "matched_scenario_count"
        ]
        == report[
            "scenario_count"
        ]
    )


def test_timeout_scenario_recovers_after_replanning():
    """Timeout should be observed and followed by successful recovery."""

    scenarios = load_failure_scenarios(
        SCENARIOS_PATH
    )

    report = run_failure_suite(
        scenarios
    )

    timeout_result = next(
        result
        for result
        in report[
            "scenarios"
        ]
        if result["id"]
        == "timeout_then_recover"
    )

    assert (
        timeout_result[
            "actual_final_status"
        ]
        == "approved_tests_applied"
    )

    assert (
        timeout_result[
            "retry_count"
        ]
        == 1
    )

    assert (
        timeout_result[
            "test_success"
        ]
        is True
    )

    assert (
        timeout_result[
            "test_execution_count"
        ]
        == 2
    )


def test_retry_limit_prevents_unbounded_loop():
    """Repeated failure must terminate at the configured retry limit."""

    scenarios = load_failure_scenarios(
        SCENARIOS_PATH
    )

    report = run_failure_suite(
        scenarios
    )

    retry_result = next(
        result
        for result
        in report[
            "scenarios"
        ]
        if result["id"]
        == "retry_limit_reached"
    )

    assert (
        retry_result[
            "actual_final_status"
        ]
        == "retry_limit_reached"
    )

    assert (
        retry_result[
            "retry_count"
        ]
        == 2
    )

    assert (
        retry_result[
            "test_execution_count"
        ]
        == 3
    )

    assert (
        retry_result[
            "approval_call_count"
        ]
        == 0
    )

    assert (
        retry_result[
            "application_call_count"
        ]
        == 0
    )


def test_fail_closed_scenarios_never_apply_candidates():
    """Malformed or unsafe LLM output must fail before application."""

    scenarios = load_failure_scenarios(
        SCENARIOS_PATH
    )

    report = run_failure_suite(
        scenarios
    )

    protected_ids = {
        "malformed_analysis_json",
        "unsafe_candidate_path",
    }

    protected_results = [
        result
        for result
        in report[
            "scenarios"
        ]
        if result[
            "id"
        ]
        in protected_ids
    ]

    assert len(
        protected_results
    ) == 2

    for result in protected_results:
        assert (
            result[
                "actual_exception"
            ]
            == "ValueError"
        )

        assert (
            result[
                "application_call_count"
            ]
            == 0
        )