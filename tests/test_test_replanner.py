from aider_agent.analysis.test_replanner import TestReplanner
from aider_agent.llm.fake_client import FakeLlmClient


REVISED_RESPONSE = """
{
  "candidate_tests": [
    {
      "file_path": "tests/test_sample.py",
      "target_file": "sample.py",
      "rationale": "Correct the failed assertion.",
      "code": "from sample import add\\n\\ndef test_add():\\n    assert add(2, 3) == 5"
    }
  ]
}
""".strip()


def test_replanner_returns_revised_candidate():
    """The replanner should return a validated revised test."""

    client = FakeLlmClient(
        responses=[
            REVISED_RESPONSE
        ]
    )

    replanner = TestReplanner(
        client
    )

    result = replanner.revise(
        staged_files=[
            "sample.py"
        ],
        staged_diff=(
            "+ return a + b"
        ),
        test_gaps=[
            "Missing addition test."
        ],
        previous_candidate_tests=[
            {
                "file_path":
                    "tests/test_sample.py",
                "target_file":
                    "sample.py",
                "rationale":
                    "Test addition.",
                "code":
                    "def test_add(): assert False",
            }
        ],
        test_stdout=(
            "FAILED test_add - AssertionError"
        ),
        test_stderr="",
        timed_out=False,
        retry_number=1,
    )

    assert len(
        result["candidate_tests"]
    ) == 1

    assert (
        "add(2, 3) == 5"
        in result["candidate_tests"][0]["code"]
    )


def test_replanner_receives_failure_observation():
    """Pytest output should be included in the replanning prompt."""

    client = FakeLlmClient(
        responses=[
            REVISED_RESPONSE
        ]
    )

    replanner = TestReplanner(
        client
    )

    replanner.revise(
        staged_files=[
            "sample.py"
        ],
        staged_diff="+ change",
        test_gaps=[
            "Missing test."
        ],
        previous_candidate_tests=[],
        test_stdout=(
            "AssertionError: expected 5 but got 6"
        ),
        test_stderr=(
            "example stderr"
        ),
        timed_out=False,
        retry_number=1,
    )

    prompt = client.calls[0][
        "user_prompt"
    ]

    assert (
        "expected 5 but got 6"
        in prompt
    )

    assert (
        "example stderr"
        in prompt
    )

    assert (
        "RETRY NUMBER:\n1"
        in prompt
    )