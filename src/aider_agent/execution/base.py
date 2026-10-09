from typing import Protocol, TypedDict


class TestExecutionResult(TypedDict):
    """Result returned after executing candidate tests."""

    success: bool
    exit_code: int | None
    stdout: str
    stderr: str
    timed_out: bool


class TestRunner(Protocol):
    """Common interface for candidate-test execution."""

    def run(
        self,
        repository_path: str,
        candidate_tests: list[dict],
    ) -> TestExecutionResult:
        """Execute candidate tests in an isolated working area."""
        ...