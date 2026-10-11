from langgraph.graph import END, START, StateGraph

from aider_agent.agent.state import AgentState
from aider_agent.analysis.candidate_test_generator import (
    CandidateTestGenerator,
)
from aider_agent.analysis.risk_analyzer import RiskAnalyzer
from aider_agent.analysis.test_replanner import TestReplanner
from aider_agent.approval.base import (
    ApprovalGate,
    CandidateApplier,
)
from aider_agent.approval.candidate_applier import (
    CandidateTestApplier,
)
from aider_agent.approval.console_gate import (
    ConsoleApprovalGate,
)
from aider_agent.execution.base import TestRunner
from aider_agent.execution.pytest_runner import PytestSandboxRunner
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

    staged_files = reader.get_staged_files()
    staged_diff = reader.get_staged_diff()

    return {
        "staged_files": staged_files,
        "staged_diff": staged_diff,
        "status": "git_read_complete",
    }


def route_after_git_read(
    state: AgentState,
) -> str:
    """Choose the next step after Git inspection."""

    if state.get("staged_files"):
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
    """Choose whether candidate tests are needed."""

    if state.get("test_gaps"):
        return "generate_candidate_tests"

    return "no_test_gaps"


def route_after_candidate_generation(
    state: AgentState,
) -> str:
    """Run candidates only when useful candidates exist."""

    if state.get("candidate_tests"):
        return "execute_candidate_tests"

    return "no_candidate_tests"


def no_changes(
    state: AgentState,
) -> dict:
    """Stop when no staged Git changes exist."""

    return {
        "status": "no_changes",
        "message": "No staged Git changes were found.",
    }


def no_test_gaps(
    state: AgentState,
) -> dict:
    """Finish when analysis finds no missing tests."""

    return {
        "candidate_tests": [],
        "status": "analysis_complete",
        "message": (
            "Risk analysis completed and "
            "no test gaps were identified."
        ),
    }


def no_candidate_tests(
    state: AgentState,
) -> dict:
    """Stop safely when the LLM cannot produce candidate tests."""

    return {
        "candidate_tests": [],
        "status": "no_candidate_tests",
        "message": (
            "No useful candidate tests could be generated. "
            "Human review is required."
        ),
    }


def build_agent_graph(
    llm_client: LlmClient,
    test_runner: TestRunner | None = None,
    approval_gate: ApprovalGate | None = None,
    candidate_applier: CandidateApplier | None = None,
    max_retries: int = 3,
):
    """Build and compile the bounded agent workflow."""

    if not isinstance(max_retries, int) or max_retries < 0:
        raise ValueError(
            "max_retries must be a non-negative integer."
        )

    risk_analyzer = RiskAnalyzer(
        llm_client
    )

    test_generator = CandidateTestGenerator(
        llm_client
    )

    test_replanner = TestReplanner(
        llm_client
    )

    runner = (
        test_runner
        if test_runner is not None
        else PytestSandboxRunner()
    )

    gate = (
        approval_gate
        if approval_gate is not None
        else ConsoleApprovalGate()
    )

    applier = (
        candidate_applier
        if candidate_applier is not None
        else CandidateTestApplier()
    )

    def analyze_risk(
        state: AgentState,
    ) -> dict:
        """Analyze staged changes for risk and test gaps."""

        analysis = risk_analyzer.analyze(
            staged_files=state.get(
                "staged_files",
                [],
            ),
            staged_diff=state.get(
                "staged_diff",
                "",
            ),
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
        """Generate initial candidate tests."""

        result = test_generator.generate(
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

        candidate_tests = result[
            "candidate_tests"
        ]

        return {
            "candidate_tests": candidate_tests,
            "retry_count": 0,
            "status": "candidate_tests_generated",
            "message": (
                f"{len(candidate_tests)} candidate "
                "test(s) generated."
            ),
        }

    def execute_candidate_tests(
        state: AgentState,
    ) -> dict:
        """Execute candidate tests inside the isolated runner."""

        result = runner.run(
            repository_path=state.get(
                "repository_path",
                ".",
            ),
            candidate_tests=state.get(
                "candidate_tests",
                [],
            ),
        )

        if result["timed_out"]:
            status = "tests_timed_out"
            message = (
                "Candidate test execution exceeded "
                "the time limit."
            )

        elif result["success"]:
            status = "tests_passed"
            message = (
                "Candidate tests completed successfully."
            )

        else:
            status = "tests_failed"
            message = (
                "Candidate tests completed with failures."
            )

        return {
            "test_success": result[
                "success"
            ],
            "test_exit_code": result[
                "exit_code"
            ],
            "test_stdout": result[
                "stdout"
            ],
            "test_stderr": result[
                "stderr"
            ],
            "test_timed_out": result[
                "timed_out"
            ],
            "status": status,
            "message": message,
        }

    def route_after_test_execution(
        state: AgentState,
    ) -> str:
        """
        Send passing tests to human approval.
        Replan failed tests when retries remain.
        """

        if state.get(
            "test_success"
        ):
            return "request_human_approval"

        retry_count = state.get(
            "retry_count",
            0,
        )

        if retry_count < max_retries:
            return "replan_candidate_tests"

        return "retry_limit_reached"

    def replan_candidate_tests(
        state: AgentState,
    ) -> dict:
        """Revise failed candidate tests using pytest observations."""

        next_retry = (
            state.get(
                "retry_count",
                0,
            )
            + 1
        )

        result = test_replanner.revise(
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
            previous_candidate_tests=state.get(
                "candidate_tests",
                [],
            ),
            test_stdout=state.get(
                "test_stdout",
                "",
            ),
            test_stderr=state.get(
                "test_stderr",
                "",
            ),
            timed_out=state.get(
                "test_timed_out",
                False,
            ),
            retry_number=next_retry,
        )

        candidate_tests = result[
            "candidate_tests"
        ]

        return {
            "candidate_tests": candidate_tests,
            "retry_count": next_retry,
            "status": "candidate_tests_replanned",
            "message": (
                f"Candidate tests revised for retry "
                f"{next_retry} of {max_retries}."
            ),
        }

    def retry_limit_reached(
        state: AgentState,
    ) -> dict:
        """Stop after the configured retry limit."""

        return {
            "status": "retry_limit_reached",
            "message": (
                f"Candidate tests still failed after "
                f"{max_retries} retry attempt(s). "
                "Human review is required."
            ),
        }

    def request_human_approval(
        state: AgentState,
    ) -> dict:
        """
        Ask a human before writing generated tests
        to the real repository.
        """

        approved = gate.request_approval(
            repository_path=state.get(
                "repository_path",
                ".",
            ),
            candidate_tests=state.get(
                "candidate_tests",
                [],
            ),
        )

        if approved:
            return {
                "approval_granted": True,
                "status": "approval_granted",
                "message": (
                    "Human reviewer approved "
                    "the candidate tests."
                ),
            }

        return {
            "approval_granted": False,
            "status": "approval_rejected",
            "message": (
                "Human reviewer rejected "
                "the candidate tests."
            ),
        }

    def route_after_approval(
        state: AgentState,
    ) -> str:
        """Apply tests only after explicit human approval."""

        if state.get(
            "approval_granted",
            False,
        ):
            return "apply_candidate_tests"

        return "approval_rejected"

    def apply_candidate_tests(
        state: AgentState,
    ) -> dict:
        """Apply approved tests to the real working repository."""

        applied_files = applier.apply(
            repository_path=state.get(
                "repository_path",
                ".",
            ),
            candidate_tests=state.get(
                "candidate_tests",
                [],
            ),
        )

        return {
            "applied_files": applied_files,
            "status": "approved_tests_applied",
            "message": (
                f"{len(applied_files)} approved test file(s) "
                "were applied to the working repository. "
                "No Git staging, commit, or push was performed."
            ),
        }

    def approval_rejected(
        state: AgentState,
    ) -> dict:
        """Stop without applying candidate tests."""

        return {
            "applied_files": [],
            "status": "approval_rejected",
            "message": (
                "Candidate tests were rejected. "
                "The working repository was not modified."
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
        "execute_candidate_tests",
        execute_candidate_tests,
    )

    builder.add_node(
        "replan_candidate_tests",
        replan_candidate_tests,
    )

    builder.add_node(
        "retry_limit_reached",
        retry_limit_reached,
    )

    builder.add_node(
        "request_human_approval",
        request_human_approval,
    )

    builder.add_node(
        "apply_candidate_tests",
        apply_candidate_tests,
    )

    builder.add_node(
        "approval_rejected",
        approval_rejected,
    )

    builder.add_node(
        "no_test_gaps",
        no_test_gaps,
    )

    builder.add_node(
        "no_candidate_tests",
        no_candidate_tests,
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
            "prepare_analysis":
                "prepare_analysis",
            "no_changes":
                "no_changes",
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

    builder.add_conditional_edges(
        "generate_candidate_tests",
        route_after_candidate_generation,
        {
            "execute_candidate_tests":
                "execute_candidate_tests",
            "no_candidate_tests":
                "no_candidate_tests",
        },
    )

    builder.add_conditional_edges(
        "execute_candidate_tests",
        route_after_test_execution,
        {
            "request_human_approval":
                "request_human_approval",
            "replan_candidate_tests":
                "replan_candidate_tests",
            "retry_limit_reached":
                "retry_limit_reached",
        },
    )

    builder.add_conditional_edges(
        "replan_candidate_tests",
        route_after_candidate_generation,
        {
            "execute_candidate_tests":
                "execute_candidate_tests",
            "no_candidate_tests":
                "no_candidate_tests",
        },
    )

    builder.add_conditional_edges(
        "request_human_approval",
        route_after_approval,
        {
            "apply_candidate_tests":
                "apply_candidate_tests",
            "approval_rejected":
                "approval_rejected",
        },
    )

    builder.add_edge(
        "apply_candidate_tests",
        END,
    )

    builder.add_edge(
        "approval_rejected",
        END,
    )

    builder.add_edge(
        "retry_limit_reached",
        END,
    )

    builder.add_edge(
        "no_test_gaps",
        END,
    )

    builder.add_edge(
        "no_candidate_tests",
        END,
    )

    builder.add_edge(
        "no_changes",
        END,
    )

    return builder.compile()