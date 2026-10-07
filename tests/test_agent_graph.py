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


def create_test_repository(
    tmp_path: Path,
) -> None:
    """Create a temporary Git repository with one committed file."""

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
    """No staged changes should stop before calling the LLM."""

    create_test_repository(
        tmp_path
    )

    client = FakeLlmClient(
        responses=[]
    )

    graph = build_agent_graph(
        client
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

    assert (
        result["staged_diff"]
        == ""
    )

    # The LLM must not be called when there are no staged changes.
    assert client.calls == []


def test_graph_analyzes_staged_changes(
    tmp_path,
):
    """
    Staged changes should be analyzed and candidate tests
    should be generated when test gaps are found.
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

    graph = build_agent_graph(
        client
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
        == "candidate_tests_generated"
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

    assert (
        result["analysis_summary"]
        == "The calculation logic changed."
    )

    assert len(
        result["candidate_tests"]
    ) == 1

    assert (
        result["candidate_tests"][0]["file_path"]
        == "tests/test_sample.py"
    )

    assert (
        result["candidate_tests"][0]["target_file"]
        == "sample.py"
    )

    # Call 1 = risk analysis
    # Call 2 = candidate test generation
    assert len(
        client.calls
    ) == 2


def test_graph_skips_generation_when_no_test_gaps(
    tmp_path,
):
    """
    The workflow should stop after analysis when
    no missing tests are identified.
    """

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
      "summary": "The change is already adequately tested."
    }
    """.strip()

    client = FakeLlmClient(
        responses=[
            no_gap_analysis
        ]
    )

    graph = build_agent_graph(
        client
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

    # Only risk analysis should have called the LLM.
    assert len(
        client.calls
    ) == 1