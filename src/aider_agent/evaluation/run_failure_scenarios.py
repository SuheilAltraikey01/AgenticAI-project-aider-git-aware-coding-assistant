import argparse
import json

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from git import Repo

from aider_agent.agent.graph import build_agent_graph
from aider_agent.evaluation.harness import (
    NoOpCandidateApplier,
    SequenceTestRunner,
    StaticApprovalGate,
)
from aider_agent.llm.fake_client import FakeLlmClient


def load_failure_scenarios(
    path: str | Path,
) -> list[dict]:
    """Load controlled failure and recovery scenarios."""

    scenario_path = Path(
        path
    )

    scenarios = json.loads(
        scenario_path.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(
        scenarios,
        list,
    ):
        raise ValueError(
            "Failure scenario file must contain a JSON list."
        )

    if not scenarios:
        raise ValueError(
            "Failure scenario set cannot be empty."
        )

    return scenarios


def create_repository(
    repository_path: Path,
    scenario: dict,
) -> None:
    """Create a temporary staged Git repository."""

    repository = scenario[
        "repository"
    ]

    file_path = repository[
        "file_path"
    ]

    target = (
        repository_path
        / Path(file_path)
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
                "Failure Scenario User",
            )

            config.set_value(
                "user",
                "email",
                "failure@example.com",
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
            "Initial failure scenario state"
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


def build_llm_responses(
    scenario: dict,
) -> list[str]:
    """Build deterministic fake LLM responses for one scenario."""

    responses = []

    if "analysis_raw" in scenario:
        responses.append(
            scenario[
                "analysis_raw"
            ]
        )

    else:
        responses.append(
            json.dumps(
                scenario[
                    "analysis_response"
                ]
            )
        )

    for candidate_response in scenario.get(
        "candidate_responses",
        [],
    ):
        responses.append(
            json.dumps(
                candidate_response
            )
        )

    return responses


def run_failure_scenario(
    scenario: dict,
) -> dict:
    """Run one controlled failure or recovery scenario."""

    with TemporaryDirectory(
        prefix="aider-failure-scenario-"
    ) as temporary_directory:

        repository_path = Path(
            temporary_directory
        )

        create_repository(
            repository_path,
            scenario,
        )

        client = FakeLlmClient(
            responses=build_llm_responses(
                scenario
            )
        )

        runner = SequenceTestRunner(
            results=scenario.get(
                "runner_results",
                [],
            )
        )

        gate = StaticApprovalGate(
            approved=scenario.get(
                "approval",
                False,
            )
        )

        applier = NoOpCandidateApplier()

        graph = build_agent_graph(
            client,
            test_runner=runner,
            approval_gate=gate,
            candidate_applier=applier,
            max_retries=scenario.get(
                "max_retries",
                3,
            ),
        )

        result = {}

        actual_exception = None

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
            actual_exception = (
                type(exc).__name__
            )

        expected_exception = scenario.get(
            "expected_exception"
        )

        expected_status = scenario.get(
            "expected_final_status"
        )

        if expected_exception is not None:
            matched = (
                actual_exception
                == expected_exception
            )

        else:
            matched = (
                actual_exception is None
                and result.get(
                    "status"
                )
                == expected_status
            )

        expected_retry_count = scenario.get(
            "expected_retry_count"
        )

        if (
            matched
            and expected_retry_count
            is not None
        ):
            matched = (
                result.get(
                    "retry_count",
                    0,
                )
                == expected_retry_count
            )

        if (
            matched
            and "expected_test_success"
            in scenario
        ):
            matched = (
                result.get(
                    "test_success"
                )
                == scenario[
                    "expected_test_success"
                ]
            )

        return {
            "id":
                scenario[
                    "id"
                ],

            "description":
                scenario.get(
                    "description",
                    "",
                ),

            "expected_final_status":
                expected_status,

            "actual_final_status":
                result.get(
                    "status"
                ),

            "expected_exception":
                expected_exception,

            "actual_exception":
                actual_exception,

            "retry_count":
                result.get(
                    "retry_count",
                    0,
                ),

            "test_success":
                result.get(
                    "test_success"
                ),

            "llm_call_count":
                len(
                    client.calls
                ),

            "test_execution_count":
                len(
                    runner.calls
                ),

            "approval_call_count":
                len(
                    gate.calls
                ),

            "application_call_count":
                len(
                    applier.calls
                ),

            "trace_created":
                bool(
                    result.get(
                        "trace_path"
                    )
                ),

            "matched_expected_outcome":
                matched,
        }


def run_failure_suite(
    scenarios: list[dict],
) -> dict:
    """Run every controlled failure scenario."""

    results = [
        run_failure_scenario(
            scenario
        )
        for scenario
        in scenarios
    ]

    passed = sum(
        1
        for result
        in results
        if result[
            "matched_expected_outcome"
        ]
    )

    return {
        "evaluation_mode":
            "offline_failure_recovery",

        "generated_at_utc":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "scenario_count":
            len(
                results
            ),

        "matched_scenario_count":
            passed,

        "all_expected_outcomes_matched":
            passed
            == len(
                results
            ),

        "scenarios":
            results,
    }


def main():
    """Run the controlled failure and recovery suite."""

    parser = argparse.ArgumentParser(
        description=(
            "Run controlled offline "
            "failure and recovery scenarios."
        )
    )

    parser.add_argument(
        "--scenarios",
        default=(
            "evaluation/"
            "failure_scenarios.json"
        ),
    )

    parser.add_argument(
        "--output",
        default=(
            "evaluation/results/"
            "failure_latest.json"
        ),
    )

    args = parser.parse_args()

    scenarios = load_failure_scenarios(
        args.scenarios
    )

    report = run_failure_suite(
        scenarios
    )

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
        "=== Failure and Recovery Evaluation ==="
    )

    print(
        "Scenarios:",
        report[
            "scenario_count"
        ],
    )

    print(
        "Expected outcomes matched:",
        (
            f"{report['matched_scenario_count']}"
            f"/{report['scenario_count']}"
        ),
    )

    print()

    for scenario in report[
        "scenarios"
    ]:
        marker = (
            "PASS"
            if scenario[
                "matched_expected_outcome"
            ]
            else "FAIL"
        )

        print(
            f"[{marker}] "
            f"{scenario['id']}"
        )

        if scenario[
            "actual_exception"
        ]:
            print(
                "  Exception:",
                scenario[
                    "actual_exception"
                ],
            )

        else:
            print(
                "  Status:",
                scenario[
                    "actual_final_status"
                ],
            )

            print(
                "  Retries:",
                scenario[
                    "retry_count"
                ],
            )

    print()
    print(
        "All expected outcomes matched:",
        report[
            "all_expected_outcomes_matched"
        ],
    )

    print(
        "Report:",
        output_path.as_posix(),
    )


if __name__ == "__main__":
    main()