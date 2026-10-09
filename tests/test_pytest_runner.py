from pathlib import Path

import pytest
from git import Repo

from aider_agent.execution.pytest_runner import (
    PytestSandboxRunner,
)


def create_repository(
    tmp_path: Path,
) -> None:
    """Create a small staged Python project for sandbox tests."""

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

        calculator = (
            tmp_path / "calculator.py"
        )

        calculator.write_text(
            "def add(a, b):\n"
            "    return a + b\n",
            encoding="utf-8",
        )

        repo.index.add(
            ["calculator.py"]
        )

        repo.index.commit(
            "Initial commit"
        )

    finally:
        repo.close()


def test_runner_executes_passing_candidate(
    tmp_path,
):
    """A valid candidate test should pass inside the sandbox."""

    create_repository(
        tmp_path
    )

    runner = PytestSandboxRunner(
        timeout_seconds=10
    )

    candidates = [
        {
            "file_path":
                "tests/test_calculator_generated.py",
            "target_file":
                "calculator.py",
            "rationale":
                "Verify addition.",
            "code":
                "from calculator import add\n\n"
                "def test_add():\n"
                "    assert add(2, 3) == 5\n",
        }
    ]

    result = runner.run(
        repository_path=str(
            tmp_path
        ),
        candidate_tests=candidates,
    )

    assert result["success"] is True
    assert result["exit_code"] == 0
    assert result["timed_out"] is False


def test_runner_captures_failing_candidate(
    tmp_path,
):
    """A failing candidate should return a controlled failure."""

    create_repository(
        tmp_path
    )

    runner = PytestSandboxRunner(
        timeout_seconds=10
    )

    candidates = [
        {
            "file_path":
                "tests/test_calculator_generated.py",
            "target_file":
                "calculator.py",
            "rationale":
                "Intentional failure.",
            "code":
                "from calculator import add\n\n"
                "def test_add():\n"
                "    assert add(2, 3) == 100\n",
        }
    ]

    result = runner.run(
        repository_path=str(
            tmp_path
        ),
        candidate_tests=candidates,
    )

    assert result["success"] is False
    assert result["exit_code"] != 0
    assert result["timed_out"] is False
    assert "failed" in result["stdout"].lower()


def test_runner_does_not_write_candidate_to_real_repo(
    tmp_path,
):
    """Generated files must exist only inside the disposable sandbox."""

    create_repository(
        tmp_path
    )

    runner = PytestSandboxRunner(
        timeout_seconds=10
    )

    candidate_path = (
        tmp_path
        / "tests"
        / "test_calculator_generated.py"
    )

    candidates = [
        {
            "file_path":
                "tests/test_calculator_generated.py",
            "target_file":
                "calculator.py",
            "rationale":
                "Verify isolation.",
            "code":
                "def test_example():\n"
                "    assert True\n",
        }
    ]

    runner.run(
        repository_path=str(
            tmp_path
        ),
        candidate_tests=candidates,
    )

    assert candidate_path.exists() is False


def test_runner_rejects_path_traversal(
    tmp_path,
):
    """The execution layer should independently reject unsafe paths."""

    create_repository(
        tmp_path
    )

    runner = PytestSandboxRunner()

    candidates = [
        {
            "file_path":
                "tests/../../danger.py",
            "target_file":
                "calculator.py",
            "rationale":
                "Unsafe example.",
            "code":
                "def test_example(): pass",
        }
    ]

    with pytest.raises(
        ValueError,
        match="cannot contain",
    ):
        runner.run(
            repository_path=str(
                tmp_path
            ),
            candidate_tests=candidates,
        )