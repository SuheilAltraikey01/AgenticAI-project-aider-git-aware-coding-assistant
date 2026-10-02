from langgraph.graph import END, START, StateGraph

from aider_agent.agent.state import AgentState
from aider_agent.git.diff_reader import GitDiffReader


def read_git_changes(state: AgentState) -> dict:
    """Read staged files and the staged diff from the repository."""

    repository_path = state.get("repository_path", ".")

    reader = GitDiffReader(repository_path)

    staged_files = reader.get_staged_files()
    staged_diff = reader.get_staged_diff()

    return {
        "staged_files": staged_files,
        "staged_diff": staged_diff,
        "status": "git_read_complete",
    }


def route_after_git_read(state: AgentState) -> str:
    """Choose the next workflow step after reading Git changes."""

    if state.get("staged_files"):
        return "prepare_analysis"

    return "no_changes"


def prepare_analysis(state: AgentState) -> dict:
    """Mark staged changes as ready for future LLM analysis."""

    staged_files = state.get("staged_files", [])

    return {
        "status": "ready_for_analysis",
        "message": (
            f"{len(staged_files)} staged file(s) are ready for analysis."
        ),
    }


def no_changes(state: AgentState) -> dict:
    """Finish the workflow when no staged changes are available."""

    return {
        "status": "no_changes",
        "message": "No staged Git changes were found.",
    }


def build_agent_graph():
    """Build and compile the initial agent workflow."""

    builder = StateGraph(AgentState)

    builder.add_node(
        "read_git_changes",
        read_git_changes,
    )

    builder.add_node(
        "prepare_analysis",
        prepare_analysis,
    )

    builder.add_node(
        "no_changes",
        no_changes,
    )

    builder.add_edge(
        START,
        "read_git_changes",
    )

    builder.add_conditional_edges(
        "read_git_changes",
        route_after_git_read,
        {
            "prepare_analysis": "prepare_analysis",
            "no_changes": "no_changes",
        },
    )

    builder.add_edge(
        "prepare_analysis",
        END,
    )

    builder.add_edge(
        "no_changes",
        END,
    )

    return builder.compile()