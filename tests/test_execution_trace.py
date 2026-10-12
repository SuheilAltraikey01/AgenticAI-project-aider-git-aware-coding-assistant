import json

from pathlib import Path

from git import Repo

from aider_agent.agent.graph import build_agent_graph
from aider_agent.llm.fake_client import FakeLlmClient


FAKE_ANALYSIS = """
{
  "risk_level": "medium",
  "risky_files": ["sample.py"],
  "test_gaps": [
    "No test covers addition."
  ],
  "summary": "Addition logic changed."
}
""".strip()


FAKE_CANDIDATE = """
{
  "candidate_tests": [
    {
      "file_path": "tests/test_sample.py",
      "target_file": "sample.py",
      "rationale": "Test addition.",
      "code": "from sample import add\\n\\ndef test_add():\\n    assert add(2, 3) == 5"
    }
  ]
}
""".strip()


class FakeTestRunner:
    """Return one passing test result."""

    def run(
        self,
        repository_path: str,
        candidate_tests: list[dict],
    ) -> dict:

        return {
            "success": True,
            "exit_code": 0,
            "stdout": "1 passed",
            "stderr": "",
            "timed_out": False,
        }


class RejectApprovalGate:
    """Reject candidates without interactive input."""

    def request_approval(
        self,
        repository_path: str,
        candidate_tests: list[dict],
    ) -> bool:

        return False


def create_repository(
    tmp_path: Path,
) -> None:
    """Create a Git repository with one staged change."""

    repo = Repo.init(
        tmp_path
    )

    try:
        with repo.config_writer() as config:
            config.set_value(
                "user",
                "name",
                "Trace Test",
            )

            config.set_value(
                "user",
                "email",
                "trace@example.com",
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


def test_graph_persists_execution_trace(
    tmp_path,
):
    """A completed workflow should produce a JSON execution trace."""

    create_repository(
        tmp_path
    )

    client = FakeLlmClient(
        responses=[
            FAKE_ANALYSIS,
            FAKE_CANDIDATE,
        ]
    )

    graph = build_agent_graph(
        client,
        test_runner=FakeTestRunner(),
        approval_gate=RejectApprovalGate(),
    )

    result = graph.invoke(
        {
            "repository_path":
                str(tmp_path)
        }
    )

    assert (
        result["status"]
        == "approval_rejected"
    )

    assert "trace_path" in result

    trace_file = (
        tmp_path
        / result["trace_path"]
    )

    assert trace_file.exists()

    trace = json.loads(
        trace_file.read_text(
            encoding="utf-8"
        )
    )

    assert (
        trace["final_status"]
        == "approval_rejected"
    )

    event_types = [
        event["type"]
        for event
        in trace["events"]
    ]

    assert (
        "git_read"
        in event_types
    )

    assert (
        "risk_analysis"
        in event_types
    )

    assert (
        "candidate_generation"
        in event_types
    )

    assert (
        "test_execution"
        in event_types
    )

    assert (
        "approval_decision"
        in event_types
    )

    assert (
        "workflow_stopped"
        in event_types
    )

    assert (
        "workflow_finished"
        in event_types
    )