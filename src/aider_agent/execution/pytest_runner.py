import os
import subprocess
import sys
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory

from git import Repo

from aider_agent.execution.base import TestExecutionResult


class PytestSandboxRunner:
    """
    Run generated candidate tests inside a disposable repository copy.

    The runner exports the Git index into a temporary directory,
    writes candidate tests only inside that directory, runs pytest,
    captures the result, and then deletes the temporary directory.

    This provides filesystem isolation but is not a complete
    operating-system security sandbox.
    """

    def __init__(
        self,
        timeout_seconds: int = 30,
    ):
        self.timeout_seconds = timeout_seconds

    def _validate_candidate_path(
        self,
        file_path: str,
    ) -> PurePosixPath:
        """Validate that a candidate path stays inside tests/."""

        path = PurePosixPath(
            file_path.replace("\\", "/")
        )

        if path.is_absolute():
            raise ValueError(
                "Candidate test path must be relative."
            )

        if ".." in path.parts:
            raise ValueError(
                "Candidate test path cannot contain '..'."
            )

        if not path.parts or path.parts[0] != "tests":
            raise ValueError(
                "Candidate test path must be inside tests/."
            )

        if path.suffix != ".py":
            raise ValueError(
                "Candidate test file must be a Python file."
            )

        return path

    def _export_git_index(
        self,
        repository_path: Path,
        sandbox_path: Path,
    ) -> None:
        """
        Export the staged Git snapshot into the sandbox.

        Using the Git index is important because the agent reviews
        staged changes, not unrelated unstaged working-tree changes.
        """

        repo = Repo(repository_path)

        try:
            prefix = sandbox_path.resolve().as_posix() + "/"

            repo.git.checkout_index(
                "--all",
                f"--prefix={prefix}",
            )

        finally:
            repo.close()

    def _write_candidate_tests(
        self,
        sandbox_path: Path,
        candidate_tests: list[dict],
    ) -> None:
        """Write generated candidate tests only into the sandbox."""

        sandbox_root = sandbox_path.resolve()

        for candidate in candidate_tests:
            candidate_path = self._validate_candidate_path(
                candidate["file_path"]
            )

            destination = (
                sandbox_path / Path(*candidate_path.parts)
            ).resolve()

            try:
                destination.relative_to(
                    sandbox_root
                )

            except ValueError as exc:
                raise ValueError(
                    "Candidate test path escapes the sandbox."
                ) from exc

            destination.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            destination.write_text(
                candidate["code"],
                encoding="utf-8",
            )

    def _build_environment(self) -> dict[str, str]:
        """
        Build a reduced environment for the pytest subprocess.

        Known LLM API secrets are removed before generated code runs.
        """

        environment = os.environ.copy()

        secret_variables = [
            "DEEPSEEK_API_KEY",
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
        ]

        for variable in secret_variables:
            environment.pop(
                variable,
                None,
            )

        environment["PYTHONNOUSERSITE"] = "1"

        return environment

    def run(
        self,
        repository_path: str,
        candidate_tests: list[dict],
    ) -> TestExecutionResult:
        """Execute candidate tests in a temporary sandbox."""

        if not candidate_tests:
            raise ValueError(
                "At least one candidate test is required."
            )

        repository = Path(
            repository_path
        ).resolve()

        with TemporaryDirectory(
            prefix="aider-test-sandbox-"
        ) as temporary_directory:

            sandbox = Path(
                temporary_directory
            )

            self._export_git_index(
                repository_path=repository,
                sandbox_path=sandbox,
            )

            self._write_candidate_tests(
                sandbox_path=sandbox,
                candidate_tests=candidate_tests,
            )

            try:
                completed = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "pytest",
                        "-q",
                    ],
                    cwd=sandbox,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                    env=self._build_environment(),
                    check=False,
                )

            except subprocess.TimeoutExpired as exc:
                stdout = (
                    exc.stdout
                    if isinstance(exc.stdout, str)
                    else ""
                )

                stderr = (
                    exc.stderr
                    if isinstance(exc.stderr, str)
                    else ""
                )

                return {
                    "success": False,
                    "exit_code": None,
                    "stdout": stdout,
                    "stderr": stderr,
                    "timed_out": True,
                }

            return {
                "success": completed.returncode == 0,
                "exit_code": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
                "timed_out": False,
            }
        