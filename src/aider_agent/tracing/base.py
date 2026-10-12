from typing import Protocol


class TraceWriter(Protocol):
    """Interface for persisting an agent execution trace."""

    def write(
        self,
        repository_path: str,
        state: dict,
    ) -> str:
        """
        Persist the execution trace and return
        the trace path relative to the repository.
        """
        ...