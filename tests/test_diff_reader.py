from pathlib import Path

import pytest
from git import Repo

from aider_agent.git.diff_reader import GitDiffReader


def create_test_repository(tmp_path: Path) -> Repo:
    """Create a temporary Git repository for testing."""

    repo = Repo.init(tmp_path)

    with repo.config_writer() as config:
        config.set_value("user", "name", "Test User")
        config.set_value("user", "email", "test@example.com")

    sample_file = tmp_path / "sample.py"

    sample_file.write_text(
        "def add(a, b):\n"
        "    return a + b\n",
        encoding="utf-8",
    )

    repo.index.add(["sample.py"])
    repo.index.commit("Initial commit")

    return repo


def test_get_staged_files(tmp_path):
    """The reader should return files currently staged for commit."""

    repo = create_test_repository(tmp_path)

    try:
        sample_file = tmp_path / "sample.py"

        sample_file.write_text(
            "def add(a, b):\n"
            "    result = a + b\n"
            "    return result\n",
            encoding="utf-8",
        )

        repo.index.add(["sample.py"])

    finally:
        repo.close()

    reader = GitDiffReader(tmp_path)

    staged_files = reader.get_staged_files()

    assert staged_files == ["sample.py"]


def test_get_staged_diff(tmp_path):
    """The reader should return the staged code changes."""

    repo = create_test_repository(tmp_path)

    try:
        sample_file = tmp_path / "sample.py"

        sample_file.write_text(
            "def add(a, b):\n"
            "    result = a + b\n"
            "    return result\n",
            encoding="utf-8",
        )

        repo.index.add(["sample.py"])

    finally:
        repo.close()

    reader = GitDiffReader(tmp_path)

    staged_diff = reader.get_staged_diff()

    assert "sample.py" in staged_diff
    assert "result = a + b" in staged_diff


def test_no_staged_changes(tmp_path):
    """The reader should return empty results when nothing is staged."""

    repo = create_test_repository(tmp_path)
    repo.close()

    reader = GitDiffReader(tmp_path)

    assert reader.get_staged_files() == []
    assert reader.get_staged_diff() == ""


def test_invalid_repository(tmp_path):
    """The reader should raise a clear error for a non-Git directory."""

    reader = GitDiffReader(tmp_path)

    with pytest.raises(ValueError, match="Not a valid Git repository"):
        reader.get_staged_diff()