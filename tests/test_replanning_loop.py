from pathlib import Path

from git import Repo

from aider_agent.agent.graph import build_agent_graph
from aider_agent.llm.fake_client import FakeLlmClient


FAKE_ANALYSIS = """
{
  "risk_level": "medium",
  "risky_files": ["sample.py"],
  "test_gaps": [
    "No test covers the modified addition logic."
  ],
  "summary": "Addition logic changed."
}
""".strip()


INITIAL_CANDIDATE = """
{
  "candidate_tests": [
    {
      "file_path": "tests/test_sample.py",
      "target_file": "sample.py",
      "rationale": "Test addition.",
      "code": "from sample import add\\n\\ndef test_add():\\n    assert add(2, 3) == 6"
    }
  ]
}
""".strip()


REVISED_CANDIDATE = """
{
  "candidate_tests": [
    {
      "file_path": "tests/test_sample.py",
      "target_file": "sample.py",
      "rationale": "Correct the failed expected value.",
      "code": "from sample import add\\n\\ndef test_add():\\n    assert add(2, 3) == 5"
    }
  ]
}
""".strip()


class SequenceTestRunner:
    """Return predefined test execution results in order."""

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

        self.calls.append(
            {
                "repository_path": repository_path,
                "candidate_tests": candidate_tests,
            }
        )

        if not self.results:
            raise RuntimeError(
                "No fake execution results remain."
            )

        return self.results.pop(
            0
        )


class FakeApprovalGate:
    """Non-interactive approval gate for replanning tests."""

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

        self.calls.append(
            {
                "repository_path": repository_path,
                "candidate_tests": candidate_tests,
            }
        )

        return self.approved


class FakeCandidateApplier:
    """Fake applier that records application requests."""

    def __init__(
        self,
    ):
        self.calls = []

    def apply(
        self,
        repository_path: str,
        candidate_tests: list[dict],
    ) -> list[str]:

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


def create_repository(
    tmp_path: Path,
) -> None:
    """Create a temporary Git repository with one staged change."""

    repo = Repo.init(
        tmp_path
    )

    try:
        with repo.config_writer() as config:
            config.set_value(
                "user",
                "name",
                "Test User",
            )

            config.set_value(
                "user",
                "email",
                "test@example.com",
            )

        sample = (
            tmp_path
            / "sample.py"
        )

        sample.write_text(
            "def add(a, b):\n"
            "    return a + b\n",
            encoding="utf-8",
        )

        repo.index.add(
            ["sample.py"]
        )

        repo.index.commit(
            "Initial commit"
        )

        sample.write_text(
            "def add(a, b):\n"
            "    result = a + b\n"
            "    return result\n",
            encoding="utf-8",
        )

        repo.index.add(
            ["sample.py"]
        )

    finally:
        repo.close()


def test_graph_replans_after_failure_then_gets_approval(
    tmp_path,
):
    """
    A failed candidate should be revised, executed again,
    approved, and then applied.
    """

    create_repository(
        tmp_path
    )

    client = FakeLlmClient(
        responses=[
            FAKE_ANALYSIS,
            INITIAL_CANDIDATE,
            REVISED_CANDIDATE,
        ]
    )

    runner = SequenceTestRunner(
        results=[
            {
                "success": False,
                "exit_code": 1,
                "stdout": (
                    "AssertionError: "
                    "assert 5 == 6"
                ),
                "stderr": "",
                "timed_out": False,
            },
            {
                "success": True,
                "exit_code": 0,
                "stdout": "1 passed",
                "stderr": "",
                "timed_out": False,
            },
        ]
    )

    gate = FakeApprovalGate(
        approved=True
    )

    applier = FakeCandidateApplier()

    graph = build_agent_graph(
        client,
        test_runner=runner,
        approval_gate=gate,
        candidate_applier=applier,
        max_retries=3,
    )

    result = graph.invoke(
        {
            "repository_path": str(
                tmp_path
            )
        }
    )

    assert (
        result["status"]
        == "approved_tests_applied"
    )

    assert (
        result["retry_count"]
        == 1
    )

    assert (
        result["approval_granted"]
        is True
    )

    assert (
        result["applied_files"]
        == [
            "tests/test_sample.py"
        ]
    )

    # Risk analysis + initial generation + one replanning call.
    assert len(
        client.calls
    ) == 3

    # Initial execution + retry execution.
    assert len(
        runner.calls
    ) == 2

    # Approval requested only after the revised test passed.
    assert len(
        gate.calls
    ) == 1

    # Candidate applied only after approval.
    assert len(
        applier.calls
    ) == 1

    second_candidate = (
        runner.calls[1][
            "candidate_tests"
        ][0]["code"]
    )

    assert (
        "add(2, 3) == 5"
        in second_candidate
    )


def test_graph_replanned_test_can_be_rejected(
    tmp_path,
):
    """
    A revised candidate may pass but must not be applied
    when the human rejects it.
    """

    create_repository(
        tmp_path
    )

    client = FakeLlmClient(
        responses=[
            FAKE_ANALYSIS,
            INITIAL_CANDIDATE,
            REVISED_CANDIDATE,
        ]
    )

    runner = SequenceTestRunner(
        results=[
            {
                "success": False,
                "exit_code": 1,
                "stdout": (
                    "AssertionError: "
                    "assert 5 == 6"
                ),
                "stderr": "",
                "timed_out": False,
            },
            {
                "success": True,
                "exit_code": 0,
                "stdout": "1 passed",
                "stderr": "",
                "timed_out": False,
            },
        ]
    )

    gate = FakeApprovalGate(
        approved=False
    )

    applier = FakeCandidateApplier()

    graph = build_agent_graph(
        client,
        test_runner=runner,
        approval_gate=gate,
        candidate_applier=applier,
        max_retries=3,
    )

    result = graph.invoke(
        {
            "repository_path": str(
                tmp_path
            )
        }
    )

    assert (
        result["status"]
        == "approval_rejected"
    )

    assert (
        result["retry_count"]
        == 1
    )

    assert (
        result["approval_granted"]
        is False
    )

    assert len(
        gate.calls
    ) == 1

    # Rejection means nothing is applied.
    assert (
        applier.calls
        == []
    )


def test_graph_stops_after_retry_limit(
    tmp_path,
):
    """The graph must stop after the configured retry limit."""

    create_repository(
        tmp_path
    )

    client = FakeLlmClient(
        responses=[
            FAKE_ANALYSIS,
            INITIAL_CANDIDATE,
            REVISED_CANDIDATE,
            REVISED_CANDIDATE,
        ]
    )

    failure = {
        "success": False,
        "exit_code": 1,
        "stdout": "AssertionError",
        "stderr": "",
        "timed_out": False,
    }

    runner = SequenceTestRunner(
        results=[
            failure,
            failure,
            failure,
        ]
    )

    gate = FakeApprovalGate(
        approved=True
    )

    applier = FakeCandidateApplier()

    graph = build_agent_graph(
        client,
        test_runner=runner,
        approval_gate=gate,
        candidate_applier=applier,
        max_retries=2,
    )

    result = graph.invoke(
        {
            "repository_path": str(
                tmp_path
            )
        }
    )

    assert (
        result["status"]
        == "retry_limit_reached"
    )

    assert (
        result["retry_count"]
        == 2
    )

    # One initial execution + two retries.
    assert len(
        runner.calls
    ) == 3

    # Risk + initial generation + two replanning calls.
    assert len(
        client.calls
    ) == 4

    # Tests never passed, so approval must never be requested.
    assert (
        gate.calls
        == []
    )

    # Nothing should be applied.
    assert (
        applier.calls
        == []
    )