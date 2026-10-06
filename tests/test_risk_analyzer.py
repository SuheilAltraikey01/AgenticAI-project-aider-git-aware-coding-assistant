import pytest

from aider_agent.analysis.risk_analyzer import RiskAnalyzer
from aider_agent.llm.fake_client import FakeLlmClient


VALID_RESPONSE = """
{
  "risk_level": "medium",
  "risky_files": ["src/payment.py"],
  "test_gaps": [
    "No test covers zero quantity."
  ],
  "summary": "The calculation logic was modified."
}
""".strip()


def test_risk_analyzer_returns_structured_result():
    """The analyzer should parse a valid structured LLM response."""

    client = FakeLlmClient(
        responses=[
            VALID_RESPONSE
        ]
    )

    analyzer = RiskAnalyzer(
        client
    )

    result = analyzer.analyze(
        staged_files=[
            "src/payment.py"
        ],
        staged_diff=(
            "+ return total / quantity"
        ),
    )

    assert result["risk_level"] == "medium"

    assert result["risky_files"] == [
        "src/payment.py"
    ]

    assert result["test_gaps"] == [
        "No test covers zero quantity."
    ]

    assert (
        result["summary"]
        == "The calculation logic was modified."
    )


def test_risk_analyzer_sends_git_diff_to_llm():
    """The analyzer should include staged Git data in the prompt."""

    client = FakeLlmClient(
        responses=[
            VALID_RESPONSE
        ]
    )

    analyzer = RiskAnalyzer(
        client
    )

    analyzer.analyze(
        staged_files=[
            "src/payment.py"
        ],
        staged_diff=(
            "+ return total / quantity"
        ),
    )

    assert len(client.calls) == 1

    prompt = client.calls[0][
        "user_prompt"
    ]

    assert "src/payment.py" in prompt

    assert (
        "return total / quantity"
        in prompt
    )


def test_risk_analyzer_rejects_invalid_json():
    """Invalid LLM output should fail safely."""

    client = FakeLlmClient(
        responses=[
            "This is not JSON."
        ]
    )

    analyzer = RiskAnalyzer(
        client
    )

    with pytest.raises(
        ValueError,
        match="not valid JSON",
    ):
        analyzer.analyze(
            staged_files=[
                "sample.py"
            ],
            staged_diff="+ change",
        )


def test_risk_analyzer_rejects_invalid_risk_level():
    """Unknown risk levels should not be accepted."""

    client = FakeLlmClient(
        responses=[
            """
            {
              "risk_level": "extreme",
              "risky_files": [],
              "test_gaps": [],
              "summary": "Example."
            }
            """
        ]
    )

    analyzer = RiskAnalyzer(
        client
    )

    with pytest.raises(
        ValueError,
        match=(
            "risk_level must be "
            "low, medium, or high"
        ),
    ):
        analyzer.analyze(
            staged_files=[
                "sample.py"
            ],
            staged_diff="+ change",
        )