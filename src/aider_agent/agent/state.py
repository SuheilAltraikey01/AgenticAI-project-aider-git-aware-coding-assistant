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

    status: str
    message: str