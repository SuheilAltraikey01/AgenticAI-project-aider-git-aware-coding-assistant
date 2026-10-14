import json

from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from tempfile import TemporaryDirectory

from git import Repo

from aider_agent.agent.graph import build_agent_graph
from aider_agent.llm.fake_client import FakeLlmClient


class SequenceTestRunner:
    """Return predefined execution results in order."""

    def __init__(
        self,
        results: list[dict],
    ):
        self.results = list(
            results
        )
        self.calls = []

    def run(
        self,
        repository_path: str,
        candidate_tests: list[dict],
    ) -> dict:
        """Return the next deterministic execution result."""

        self.calls.append(
            {
                "repository_path": repository_path,
                "candidate_tests": candidate_tests,
            }
        )

        if not self.results:
            raise RuntimeError(
                "Evaluation runner has no results remaining."
            )

        return self.results.pop(
            0
        )


class StaticApprovalGate:
    """Return a predefined approval decision."""

    def __init__(
        self,
        approved: bool,
    ):
        self.approved = approved
        self.calls = []

    def request_approval(
        self,
        repository_path: str,
        candidate_tests: list[dict],
    ) -> bool:
        """Return the configured approval decision."""

        self.calls.append(
            {
                "repository_path": repository_path,
                "candidate_tests": candidate_tests,
            }
        )

        return self.approved


class NoOpCandidateApplier:
    """Record approved candidates without modifying evaluation repos."""

    def __init__(
        self,
    ):
        self.calls = []

    def apply(
        self,
        repository_path: str,
        candidate_tests: list[dict],
    ) -> list[str]:
        """Return candidate paths without writing files."""

        self.calls.append(
            {
                "repository_path": repository_path,
                "candidate_tests": candidate_tests,
            }
        )

        return [
            candidate["file_path"]
            for candidate in candidate_tests
        ]


def load_tasks(
    tasks_path: str | Path,
) -> list[dict]:
    """Load controlled evaluation tasks from JSON."""

    path = Path(
        tasks_path
    )

    data = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(
        data,
        list,
    ):
        raise ValueError(
            "Evaluation task file must contain a JSON list."
        )

    if not data:
        raise ValueError(
            "Evaluation task set cannot be empty."
        )

    return data


class EvaluationHarness:
    """Run deterministic controlled evaluations of the agent workflow."""

    def __init__(
        self,
        tasks: list[dict],
    ):
        if not tasks:
            raise ValueError(
                "At least one evaluation task is required."
            )

        self.tasks = tasks

    def _create_repository(
        self,
        repository_path: Path,
        task: dict,
    ) -> None:
        """Create a temporary Git repository for one task."""

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
                    "Evaluation User",
                )

                config.set_value(
                    "user",
                    "email",
                    "evaluation@example.com",
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
                "Initial evaluation state"
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

    def _build_fake_client(
        self,
        task: dict,
    ) -> FakeLlmClient:
        """Build deterministic LLM responses for one task."""

        responses = [
            json.dumps(
                task[
                    "analysis_response"
                ]
            )
        ]

        for candidate_response in task.get(
            "candidate_responses",
            [],
        ):
            responses.append(
                json.dumps(
                    candidate_response
                )
            )

        return FakeLlmClient(
            responses=responses
        )

    def _candidate_expectation_match(
        self,
        task: dict,
        result: dict,
    ) -> bool | None:
        """Check a simple controlled candidate-quality oracle."""

        expected_fragment = task.get(
            "expected_candidate_contains"
        )

        if expected_fragment is None:
            return None

        candidate_tests = result.get(
            "candidate_tests",
            [],
        )

        combined_code = "\n".join(
            candidate.get(
                "code",
                "",
            )
            for candidate
            in candidate_tests
        )

        return (
            expected_fragment
            in combined_code
        )

    def _run_task(
        self,
        task: dict,
    ) -> dict:
        """Run one controlled evaluation task."""

        with TemporaryDirectory(
            prefix="aider-eval-"
        ) as temporary_directory:

            repository_path = Path(
                temporary_directory
            )

            self._create_repository(
                repository_path,
                task,
            )

            client = self._build_fake_client(
                task
            )

            runner = SequenceTestRunner(
                results=task.get(
                    "runner_results",
                    [],
                )
            )

            gate = StaticApprovalGate(
                approved=task.get(
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
                max_retries=task.get(
                    "max_retries",
                    3,
                ),
            )

            result = graph.invoke(
                {
                    "repository_path":
                        str(repository_path)
                }
            )

            detected_gap = bool(
                result.get(
                    "test_gaps",
                    [],
                )
            )

            expected_gap = bool(
                task[
                    "expected_test_gap"
                ]
            )

            return {
                "id": task[
                    "id"
                ],
                "description": task.get(
                    "description",
                    "",
                ),
                "expected_test_gap":
                    expected_gap,
                "detected_test_gap":
                    detected_gap,
                "gap_detection_correct":
                    detected_gap == expected_gap,
                "expected_final_status":
                    task[
                        "expected_final_status"
                    ],
                "actual_final_status":
                    result.get(
                        "status"
                    ),
                "final_status_correct":
                    result.get(
                        "status"
                    )
                    == task[
                        "expected_final_status"
                    ],
                "candidate_expectation_match":
                    self._candidate_expectation_match(
                        task,
                        result,
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
                "approval_granted":
                    result.get(
                        "approval_granted"
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
                "trace_event_count":
                    len(
                        result.get(
                            "trace_events",
                            [],
                        )
                    ),
            }

    def _calculate_metrics(
        self,
        results: list[dict],
    ) -> dict:
        """Calculate aggregate evaluation metrics."""

        positive_tasks = [
            result
            for result
            in results
            if result[
                "expected_test_gap"
            ]
        ]

        negative_tasks = [
            result
            for result
            in results
            if not result[
                "expected_test_gap"
            ]
        ]

        true_positives = sum(
            1
            for result
            in positive_tasks
            if result[
                "detected_test_gap"
            ]
        )

        false_positives = sum(
            1
            for result
            in negative_tasks
            if result[
                "detected_test_gap"
            ]
        )

        detection_rate = (
            true_positives
            / len(
                positive_tasks
            )
            if positive_tasks
            else 0.0
        )

        false_positive_rate = (
            false_positives
            / len(
                negative_tasks
            )
            if negative_tasks
            else 0.0
        )

        final_status_accuracy = (
            sum(
                1
                for result
                in results
                if result[
                    "final_status_correct"
                ]
            )
            / len(
                results
            )
        )

        quality_results = [
            result[
                "candidate_expectation_match"
            ]
            for result
            in results
            if result[
                "candidate_expectation_match"
            ]
            is not None
        ]

        candidate_quality_proxy_rate = (
            sum(
                1
                for matched
                in quality_results
                if matched
            )
            / len(
                quality_results
            )
            if quality_results
            else 0.0
        )

        execution_tasks = [
            result
            for result
            in results
            if result[
                "test_execution_count"
            ] > 0
        ]

        converged_tasks = [
            result
            for result
            in execution_tasks
            if result[
                "test_success"
            ]
            is True
        ]

        convergence_rate = (
            len(
                converged_tasks
            )
            / len(
                execution_tasks
            )
            if execution_tasks
            else 0.0
        )

        average_retry_count = (
            mean(
                result[
                    "retry_count"
                ]
                for result
                in execution_tasks
            )
            if execution_tasks
            else 0.0
        )

        average_retries_to_convergence = (
            mean(
                result[
                    "retry_count"
                ]
                for result
                in converged_tasks
            )
            if converged_tasks
            else 0.0
        )

        retry_limit_count = sum(
            1
            for result
            in results
            if result[
                "actual_final_status"
            ]
            == "retry_limit_reached"
        )

        return {
            "test_gap_detection_rate":
                detection_rate,
            "false_positive_rate":
                false_positive_rate,
            "candidate_quality_proxy_rate":
                candidate_quality_proxy_rate,
            "convergence_rate":
                convergence_rate,
            "final_status_accuracy":
                final_status_accuracy,
            "average_retry_count":
                average_retry_count,
            "average_retries_to_convergence":
                average_retries_to_convergence,
            "retry_limit_count":
                retry_limit_count,
        }

    def run(
        self,
    ) -> dict:
        """Run all tasks and return a reproducible evaluation report."""

        results = [
            self._run_task(
                task
            )
            for task
            in self.tasks
        ]

        return {
            "evaluation_mode":
                "offline_deterministic",
            "generated_at_utc":
                datetime.now(
                    timezone.utc
                ).isoformat(),
            "task_count":
                len(
                    results
                ),
            "metrics":
                self._calculate_metrics(
                    results
                ),
            "tasks":
                results,
        }