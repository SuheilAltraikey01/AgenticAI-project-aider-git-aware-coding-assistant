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


def create_test_repository(
    tmp_path: Path,
) -> None:
    """Create a temporary Git repository."""

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

        sample_file = (
            tmp_path / "sample.py"
        )

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

    sample_file = (
        tmp_path / "sample.py"
    )

    sample_file.write_text(
        "def add(a, b):\n"
        "    result = a + b\n"
        "    return result\n",
        encoding="utf-8",
    )

    repo = Repo(
        tmp_path
    )

    try:
        repo.index.add(
            ["sample.py"]
        )

    finally:
        repo.close()


def test_graph_stops_when_no_changes_are_staged(
    tmp_path,
):
    """No changes should stop before calling the LLM."""

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

    assert client.calls == []


def test_graph_analyzes_staged_changes(
    tmp_path,
):
    """Staged changes should reach the risk-analysis node."""

    create_test_repository(
        tmp_path
    )

    stage_test_change(
        tmp_path
    )

    client = FakeLlmClient(
        responses=[
            FAKE_ANALYSIS
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
        result["risk_level"]
        == "medium"
    )

    assert result["risky_files"] == [
        "sample.py"
    ]

    assert len(
        result["test_gaps"]
    ) == 1

    assert (
        result["analysis_summary"]
        == "The calculation logic changed."
    )

    assert len(
        client.calls
    ) == 1