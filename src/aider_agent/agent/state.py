from typing import TypedDict


class AgentState(TypedDict, total=False):
    """State shared between the nodes of the agent workflow."""

    repository_path: str

    staged_files: list[str]
    staged_diff: str

    risk_level: str
    risky_files: list[str]
    test_gaps: list[str]
    analysis_summary: str

    candidate_tests: list[dict]

    test_success: bool
    test_exit_code: int | None
    test_stdout: str
    test_stderr: str
    test_timed_out: bool

    retry_count: int
    approval_granted: bool
    applied_files: list[str]
    status: str
    message: str