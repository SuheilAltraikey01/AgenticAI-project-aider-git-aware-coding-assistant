from aider_agent.approval.console_gate import (
    ConsoleApprovalGate,
)


CANDIDATE = {
    "file_path": "tests/test_sample.py",
    "target_file": "sample.py",
    "rationale": "Test the sample behavior.",
    "code": (
        "def test_sample():\n"
        "    assert True\n"
    ),
}


def test_gate_approves_when_user_selects_a(
    tmp_path,
    monkeypatch,
):
    """Explicit A should approve the candidate."""

    monkeypatch.setattr(
        "builtins.input",
        lambda _: "a",
    )

    gate = ConsoleApprovalGate()

    approved = gate.request_approval(
        repository_path=str(
            tmp_path
        ),
        candidate_tests=[
            CANDIDATE
        ],
    )

    assert approved is True


def test_gate_rejects_when_user_selects_r(
    tmp_path,
    monkeypatch,
):
    """Explicit R should reject the candidate."""

    monkeypatch.setattr(
        "builtins.input",
        lambda _: "r",
    )

    gate = ConsoleApprovalGate()

    approved = gate.request_approval(
        repository_path=str(
            tmp_path
        ),
        candidate_tests=[
            CANDIDATE
        ],
    )

    assert approved is False


def test_gate_can_view_diff_then_approve(
    tmp_path,
    monkeypatch,
    capsys,
):
    """V should display a diff and ask again."""

    answers = iter(
        [
            "v",
            "a",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(
            answers
        ),
    )

    gate = ConsoleApprovalGate()

    approved = gate.request_approval(
        repository_path=str(
            tmp_path
        ),
        candidate_tests=[
            CANDIDATE
        ],
    )

    output = capsys.readouterr().out

    assert approved is True
    assert "Candidate Test Diff" in output
    assert "test_sample.py" in output