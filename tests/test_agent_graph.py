from pathlib import Path

from git import Repo

from aider_agent.agent.graph import build_agent_graph
from aider_agent.llm.fake_client import FakeLlmClient


FAKE_ANALYSIS = """
{
  "risk_level": "medium",
  "risky_files": ["sample.py"],
  "test_gaps": [
    "No test covers the modified calculation."
  ],
  "summary": "The calculation logic changed."
}
""".strip()


FAKE_CANDIDATE_TESTS = """
{
  "candidate_tests": [
    {
      "file_path": "tests/test_sample.py",
      "target_file": "sample.py",
      "rationale": "Covers the modified calculation.",
      "code": "def test_add():\\n    assert True"
    }
  ]
}
""".strip()


class FakeTestRunner:
    """Deterministic test runner used by workflow tests."""

    def __init__(
        self,
        result: dict,
    ):
        self.result = result
        self.calls = []

    def run(
        self,
        repository_path: str,
        candidate_tests: list[dict],
    ) -> dict:
        """Return a predefined execution result."""

        self.calls.append(
            {
                "repository_path": repository_path,
                "candidate_tests": candidate_tests,
            }
        )

        return self.result


def create_test_repository(
    tmp_path: Path,
) -> None:
    """Create a temporary Git repository."""

    repo = Repo.init(tmp_path)

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

        sample_file = tmp_path / "sample.py"

        sample_file.write_text(
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

    finally:
        repo.close()


def stage_test_change(
    tmp_path: Path,
) -> None:
    """Modify and stage the sample file."""

    sample_file = tmp_path / "sample.py"

    sample_file.write_text(
        "def add(a, b):\n"
        "    result = a + b\n"
        "    return result\n",
        encoding="utf-8",
    )

    repo = Repo(tmp_path)

    try:
        repo.index.add(
            ["sample.py"]
        )

    finally:
        repo.close()


def test_graph_stops_when_no_changes_are_staged(
    tmp_path,
):
    """The graph should stop without calling LLM or test runner."""

    create_test_repository(
        tmp_path
    )

    client = FakeLlmClient(
        responses=[]
    )

    runner = FakeTestRunner(
        {
            "success": True,
            "exit_code": 0,
            "stdout": "",
            "stderr": "",
            "timed_out": False,
        }
    )

    graph = build_agent_graph(
        client,
        test_runner=runner,
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
        == "no_changes"
    )

    assert (
        result["staged_files"]
        == []
    )

    assert client.calls == []
    assert runner.calls == []


def test_graph_analyzes_staged_changes(
    tmp_path,
):
    """
    Staged changes should be analyzed, candidate tests generated,
    and candidate tests executed.
    """

    create_test_repository(
        tmp_path
    )

    stage_test_change(
        tmp_path
    )

    client = FakeLlmClient(
        responses=[
            FAKE_ANALYSIS,
            FAKE_CANDIDATE_TESTS,
        ]
    )

    runner = FakeTestRunner(
        {
            "success": True,
            "exit_code": 0,
            "stdout": "1 passed",
            "stderr": "",
            "timed_out": False,
        }
    )

    graph = build_agent_graph(
        client,
        test_runner=runner,
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
        == "tests_passed"
    )

    assert (
        result["risk_level"]
        == "medium"
    )

    assert (
        result["risky_files"]
        == ["sample.py"]
    )

    assert (
        result["test_gaps"]
        == [
            "No test covers the modified calculation."
        ]
    )

    assert len(
        result["candidate_tests"]
    ) == 1

    assert (
        result["candidate_tests"][0]["file_path"]
        == "tests/test_sample.py"
    )

    assert (
        result["test_success"]
        is True
    )

    assert (
        result["test_exit_code"]
        == 0
    )

    assert (
        result["test_timed_out"]
        is False
    )

    # Risk analysis + candidate generation
    assert len(
        client.calls
    ) == 2

    # Candidate execution
    assert len(
        runner.calls
    ) == 1


def test_graph_skips_generation_when_no_test_gaps(
    tmp_path,
):
    """No candidate tests should be generated when no gaps exist."""

    create_test_repository(
        tmp_path
    )

    stage_test_change(
        tmp_path
    )

    no_gap_analysis = """
    {
      "risk_level": "low",
      "risky_files": [],
      "test_gaps": [],
      "summary": "The change is adequately tested."
    }
    """.strip()

    client = FakeLlmClient(
        responses=[
            no_gap_analysis
        ]
    )

    runner = FakeTestRunner(
        {
            "success": True,
            "exit_code": 0,
            "stdout": "",
            "stderr": "",
            "timed_out": False,
        }
    )

    graph = build_agent_graph(
        client,
        test_runner=runner,
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
        == "analysis_complete"
    )

    assert (
        result["candidate_tests"]
        == []
    )

    # Only risk analysis should call the LLM.
    assert len(
        client.calls
    ) == 1

    # No candidate tests means no execution.
    assert runner.calls == []