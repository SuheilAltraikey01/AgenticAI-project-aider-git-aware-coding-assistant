from langgraph.graph import END, START, StateGraph

from aider_agent.agent.state import AgentState
from aider_agent.analysis.candidate_test_generator import (
    CandidateTestGenerator,
)
from aider_agent.analysis.risk_analyzer import RiskAnalyzer
from aider_agent.git.diff_reader import GitDiffReader
from aider_agent.llm.base import LlmClient


def read_git_changes(
    state: AgentState,
) -> dict:
    """Read staged files and staged diff from the repository."""

    repository_path = state.get(
        "repository_path",
        ".",
    )

    reader = GitDiffReader(
        repository_path
    )

    staged_files = (
        reader.get_staged_files()
    )

    staged_diff = (
        reader.get_staged_diff()
    )

    return {
        "staged_files": staged_files,
        "staged_diff": staged_diff,
        "status": "git_read_complete",
    }


def route_after_git_read(
    state: AgentState,
) -> str:
    """Choose the next step after Git inspection."""

    if state.get(
        "staged_files"
    ):
        return "prepare_analysis"

    return "no_changes"


def prepare_analysis(
    state: AgentState,
) -> dict:
    """Mark staged changes as ready for risk analysis."""

    staged_files = state.get(
        "staged_files",
        [],
    )

    return {
        "status": "ready_for_analysis",
        "message": (
            f"{len(staged_files)} staged file(s) "
            "are ready for analysis."
        ),
    }


def route_after_analysis(
    state: AgentState,
) -> str:
    """Decide whether candidate tests should be generated."""

    if state.get(
        "test_gaps"
    ):
        return "generate_candidate_tests"

    return "no_test_gaps"


def no_changes(
    state: AgentState,
) -> dict:
    """Stop when no staged Git changes exist."""

    return {
        "status": "no_changes",
        "message": (
            "No staged Git changes were found."
        ),
    }


def no_test_gaps(
    state: AgentState,
) -> dict:
    """Finish when analysis finds no test gaps."""

    return {
        "candidate_tests": [],
        "status": "analysis_complete",
        "message": (
            "Risk analysis completed and "
            "no test gaps were identified."
        ),
    }


def build_agent_graph(
    llm_client: LlmClient,
):
    """Build and compile the agent workflow."""

    risk_analyzer = RiskAnalyzer(
        llm_client
    )

    test_generator = (
        CandidateTestGenerator(
            llm_client
        )
    )

    def analyze_risk(
        state: AgentState,
    ) -> dict:
        """Analyze staged changes for risks and test gaps."""

        analysis = (
            risk_analyzer.analyze(
                staged_files=state.get(
                    "staged_files",
                    [],
                ),
                staged_diff=state.get(
                    "staged_diff",
                    "",
                ),
            )
        )

        return {
            "risk_level": analysis[
                "risk_level"
            ],
            "risky_files": analysis[
                "risky_files"
            ],
            "test_gaps": analysis[
                "test_gaps"
            ],
            "analysis_summary": analysis[
                "summary"
            ],
            "status": "analysis_complete",
            "message": (
                "Risk and test-gap analysis completed."
            ),
        }

    def generate_candidate_tests(
        state: AgentState,
    ) -> dict:
        """Generate candidate tests for identified test gaps."""

        result = (
            test_generator.generate(
                staged_files=state.get(
                    "staged_files",
                    [],
                ),
                staged_diff=state.get(
                    "staged_diff",
                    "",
                ),
                test_gaps=state.get(
                    "test_gaps",
                    [],
                ),
                risk_level=state.get(
                    "risk_level",
                    "low",
                ),
                analysis_summary=state.get(
                    "analysis_summary",
                    "",
                ),
            )
        )

        candidate_tests = (
            result[
                "candidate_tests"
            ]
        )

        return {
            "candidate_tests": candidate_tests,
            "status": "candidate_tests_generated",
            "message": (
                f"{len(candidate_tests)} candidate "
                "test(s) generated."
            ),
        }

    builder = StateGraph(
        AgentState
    )

    builder.add_node(
        "read_git_changes",
        read_git_changes,
    )

    builder.add_node(
        "prepare_analysis",
        prepare_analysis,
    )

    builder.add_node(
        "analyze_risk",
        analyze_risk,
    )

    builder.add_node(
        "generate_candidate_tests",
        generate_candidate_tests,
    )

    builder.add_node(
        "no_test_gaps",
        no_test_gaps,
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
        "analyze_risk",
    )

    builder.add_conditional_edges(
        "analyze_risk",
        route_after_analysis,
        {
            "generate_candidate_tests":
                "generate_candidate_tests",
            "no_test_gaps":
                "no_test_gaps",
        },
    )

    builder.add_edge(
        "generate_candidate_tests",
        END,
    )

    builder.add_edge(
        "no_test_gaps",
        END,
    )

    builder.add_edge(
        "no_changes",
        END,
    )

    return builder.compile()