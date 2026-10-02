from pathlib import Path

from git import Repo

from aider_agent.agent.graph import build_agent_graph


def create_test_repository(tmp_path: Path) -> None:
    """Create a temporary Git repository with one committed file."""

    repo = Repo.init(tmp_path)

    try:
        with repo.config_writer() as config:
            config.set_value("user", "name", "Test User")
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

        repo.index.add(["sample.py"])
        repo.index.commit("Initial commit")

    finally:
        repo.close()


def stage_test_change(tmp_path: Path) -> None:
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
        repo.index.add(["sample.py"])

    finally:
        repo.close()


def test_graph_stops_when_no_changes_are_staged(tmp_path):
    """The workflow should stop when there are no staged changes."""

    create_test_repository(tmp_path)

    graph = build_agent_graph()

    result = graph.invoke(
        {
            "repository_path": str(tmp_path),
        }
    )

    assert result["status"] == "no_changes"
    assert result["staged_files"] == []
    assert result["staged_diff"] == ""

    assert (
        result["message"]
        == "No staged Git changes were found."
    )


def test_graph_routes_staged_changes_to_analysis(tmp_path):
    """The workflow should route staged changes toward analysis."""

    create_test_repository(tmp_path)
    stage_test_change(tmp_path)

    graph = build_agent_graph()

    result = graph.invoke(
        {
            "repository_path": str(tmp_path),
        }
    )

    assert result["status"] == "ready_for_analysis"

    assert result["staged_files"] == [
        "sample.py"
    ]

    assert "result = a + b" in result["staged_diff"]

    assert (
        result["message"]
        == "1 staged file(s) are ready for analysis."
    )