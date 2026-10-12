import json

from aider_agent.tracing.json_trace_writer import (
    JsonTraceWriter,
)


def test_json_trace_writer_creates_structured_trace(
    tmp_path,
):
    """The writer should persist a structured JSON trace."""

    writer = JsonTraceWriter()

    state = {
        "status": "approved_tests_applied",
        "message": "Completed.",
        "staged_files": [
            "sample.py"
        ],
        "staged_diff": (
            "+def add(a, b):\n"
            "+    return a + b\n"
        ),
        "risk_level": "medium",
        "risky_files": [
            "sample.py"
        ],
        "test_gaps": [
            "Missing addition test."
        ],
        "analysis_summary": (
            "Addition logic changed."
        ),
        "candidate_tests": [
            {
                "file_path":
                    "tests/test_sample.py",
                "target_file":
                    "sample.py",
                "rationale":
                    "Test addition.",
                "code":
                    "def test_add():\n"
                    "    assert True\n",
            }
        ],
        "test_success": True,
        "test_exit_code": 0,
        "test_stdout": "1 passed",
        "test_stderr": "",
        "test_timed_out": False,
        "retry_count": 1,
        "approval_granted": True,
        "applied_files": [
            "tests/test_sample.py"
        ],
        "trace_events": [
            {
                "timestamp_utc":
                    "2026-01-01T00:00:00+00:00",
                "type":
                    "test_execution",
                "details": {
                    "success": True
                },
            }
        ],
    }

    relative_path = writer.write(
        repository_path=str(
            tmp_path
        ),
        state=state,
    )

    trace_file = (
        tmp_path
        / relative_path
    )

    assert trace_file.exists()

    data = json.loads(
        trace_file.read_text(
            encoding="utf-8"
        )
    )

    assert (
        data["schema_version"]
        == 1
    )

    assert (
        data["final_status"]
        == "approved_tests_applied"
    )

    assert (
        data["input"]["staged_files"]
        == ["sample.py"]
    )

    assert (
        data["analysis"]["risk_level"]
        == "medium"
    )

    assert (
        data["retry"]["count"]
        == 1
    )

    assert (
        data["approval"]["granted"]
        is True
    )

    assert (
        data["execution"]["success"]
        is True
    )

    assert len(
        data["input"][
            "staged_diff_sha256"
        ]
    ) == 64


def test_trace_does_not_store_raw_staged_diff(
    tmp_path,
):
    """Raw staged source code should not be copied into the trace."""

    writer = JsonTraceWriter()

    secret_diff_content = (
        "VERY_PRIVATE_SOURCE_CONTENT_123"
    )

    relative_path = writer.write(
        repository_path=str(
            tmp_path
        ),
        state={
            "status": "no_changes",
            "staged_diff":
                secret_diff_content,
        },
    )

    trace_file = (
        tmp_path
        / relative_path
    )

    raw_trace = trace_file.read_text(
        encoding="utf-8"
    )

    assert (
        secret_diff_content
        not in raw_trace
    )