import pytest

from aider_agent.analysis.candidate_test_generator import (
    CandidateTestGenerator,
)
from aider_agent.llm.fake_client import FakeLlmClient


VALID_RESPONSE = """
{
  "candidate_tests": [
    {
      "file_path": "tests/test_payment.py",
      "target_file": "src/payment.py",
      "rationale": "Covers zero quantity behavior.",
      "code": "def test_zero_quantity():\\n    assert True"
    }
  ]
}
""".strip()


def test_generator_returns_candidate_tests():
    """The generator should return validated candidate tests."""

    client = FakeLlmClient(
        responses=[
            VALID_RESPONSE
        ]
    )

    generator = CandidateTestGenerator(
        client
    )

    result = generator.generate(
        staged_files=[
            "src/payment.py"
        ],
        staged_diff=(
            "+ return total / quantity"
        ),
        test_gaps=[
            "No test covers zero quantity."
        ],
        risk_level="medium",
        analysis_summary=(
            "Calculation logic changed."
        ),
    )

    candidates = result[
        "candidate_tests"
    ]

    assert len(
        candidates
    ) == 1

    assert (
        candidates[0]["file_path"]
        == "tests/test_payment.py"
    )

    assert (
        candidates[0]["target_file"]
        == "src/payment.py"
    )

    assert (
        "zero quantity"
        in candidates[0]["rationale"]
    )


def test_generator_sends_test_gaps_to_llm():
    """Test gaps should be included in the LLM prompt."""

    client = FakeLlmClient(
        responses=[
            VALID_RESPONSE
        ]
    )

    generator = CandidateTestGenerator(
        client
    )

    generator.generate(
        staged_files=[
            "src/payment.py"
        ],
        staged_diff="+ change",
        test_gaps=[
            "Missing zero quantity test."
        ],
        risk_level="medium",
        analysis_summary="Changed logic.",
    )

    prompt = client.calls[0][
        "user_prompt"
    ]

    assert (
        "Missing zero quantity test."
        in prompt
    )


def test_generator_rejects_invalid_json():
    """Invalid model output should fail safely."""

    client = FakeLlmClient(
        responses=[
            "not json"
        ]
    )

    generator = CandidateTestGenerator(
        client
    )

    with pytest.raises(
        ValueError,
        match="not valid JSON",
    ):
        generator.generate(
            staged_files=[
                "sample.py"
            ],
            staged_diff="+ change",
            test_gaps=[
                "Missing test."
            ],
            risk_level="medium",
            analysis_summary="Example.",
        )


def test_generator_rejects_path_outside_tests():
    """Candidate files outside tests/ must be rejected."""

    client = FakeLlmClient(
        responses=[
            """
            {
              "candidate_tests": [
                {
                  "file_path": "src/payment.py",
                  "target_file": "src/payment.py",
                  "rationale": "Bad path example.",
                  "code": "def test_example(): pass"
                }
              ]
            }
            """
        ]
    )

    generator = CandidateTestGenerator(
        client
    )

    with pytest.raises(
        ValueError,
        match="inside tests/",
    ):
        generator.generate(
            staged_files=[
                "src/payment.py"
            ],
            staged_diff="+ change",
            test_gaps=[
                "Missing test."
            ],
            risk_level="high",
            analysis_summary="Example.",
        )


def test_generator_rejects_path_traversal():
    """Parent-directory path traversal must be rejected."""

    client = FakeLlmClient(
        responses=[
            """
            {
              "candidate_tests": [
                {
                  "file_path": "tests/../../danger.py",
                  "target_file": "src/payment.py",
                  "rationale": "Unsafe path.",
                  "code": "def test_example(): pass"
                }
              ]
            }
            """
        ]
    )

    generator = CandidateTestGenerator(
        client
    )

    with pytest.raises(
        ValueError,
        match="cannot contain",
    ):
        generator.generate(
            staged_files=[
                "src/payment.py"
            ],
            staged_diff="+ change",
            test_gaps=[
                "Missing test."
            ],
            risk_level="high",
            analysis_summary="Example.",
        )