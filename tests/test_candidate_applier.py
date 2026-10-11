import pytest
from git import Repo

from aider_agent.approval.candidate_applier import (
    CandidateTestApplier,
)


def test_applier_writes_approved_test(
    tmp_path,
):
    """An approved test should be written to tests/."""

    applier = CandidateTestApplier()

    candidate = {
        "file_path":
            "tests/test_sample.py",
        "target_file":
            "sample.py",
        "rationale":
            "Test example.",
        "code":
            "def test_sample():\n"
            "    assert True\n",
    }

    applied = applier.apply(
        repository_path=str(
            tmp_path
        ),
        candidate_tests=[
            candidate
        ],
    )

    destination = (
        tmp_path
        / "tests"
        / "test_sample.py"
    )

    assert destination.exists()

    assert (
        destination.read_text(
            encoding="utf-8"
        )
        == candidate["code"]
    )

    assert applied == [
        "tests/test_sample.py"
    ]


def test_applier_rejects_path_traversal(
    tmp_path,
):
    """Approved input must still pass path validation."""

    applier = CandidateTestApplier()

    candidate = {
        "file_path":
            "tests/../../danger.py",
        "target_file":
            "sample.py",
        "rationale":
            "Unsafe example.",
        "code":
            "def test_example(): pass",
    }

    with pytest.raises(
        ValueError,
        match="cannot contain",
    ):
        applier.apply(
            repository_path=str(
                tmp_path
            ),
            candidate_tests=[
                candidate
            ],
        )


def test_applier_does_not_stage_or_commit(
    tmp_path,
):
    """Applying a candidate must not stage it automatically."""

    repo = Repo.init(
        tmp_path
    )

    try:
        with repo.config_writer() as config:
            config.set_value(
                "user",
                "name",
                "Test User",
            )

            config.set_value(
                "user",
                "email",
                "test@example.com",
            )

        sample = (
            tmp_path
            / "sample.py"
        )

        sample.write_text(
            "def example():\n"
            "    return True\n",
            encoding="utf-8",
        )

        repo.index.add(
            ["sample.py"]
        )

        repo.index.commit(
            "Initial commit"
        )

        applier = (
            CandidateTestApplier()
        )

        applier.apply(
            repository_path=str(
                tmp_path
            ),
            candidate_tests=[
                {
                    "file_path":
                        "tests/test_sample.py",
                    "target_file":
                        "sample.py",
                    "rationale":
                        "Test example.",
                    "code":
                        "def test_sample():\n"
                        "    assert True\n",
                }
            ],
        )

        staged_files = repo.git.diff(
            "--cached",
            "--name-only",
        )

        assert (
            "tests/test_sample.py"
            not in staged_files
        )

        assert (
            "tests/test_sample.py"
            in repo.untracked_files
        )

    finally:
        repo.close()