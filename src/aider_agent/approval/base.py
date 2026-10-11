from typing import Protocol


class ApprovalGate(Protocol):
    """Interface for human approval before consequential actions."""

    def request_approval(
        self,
        repository_path: str,
        candidate_tests: list[dict],
    ) -> bool:
        """Return True only when the human explicitly approves."""
        ...


class CandidateApplier(Protocol):
    """Interface for applying approved candidate tests."""

    def apply(
        self,
        repository_path: str,
        candidate_tests: list[dict],
    ) -> list[str]:
        """Apply approved candidate tests and return affected paths."""
        ...