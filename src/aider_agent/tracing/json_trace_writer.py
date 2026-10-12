import hashlib
import json

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


MAX_TRACE_TEXT_CHARS = 8000


def _truncate_text(
    value: str,
) -> str:
    """Limit potentially large execution output stored in traces."""

    if len(value) <= MAX_TRACE_TEXT_CHARS:
        return value

    return (
        value[:MAX_TRACE_TEXT_CHARS]
        + "\n...[trace output truncated]..."
    )


def _sha256_text(
    value: str,
) -> str | None:
    """Return a SHA-256 digest for non-empty text."""

    if not value:
        return None

    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


class JsonTraceWriter:
    """Persist a structured local JSON trace for one agent run."""

    def __init__(
        self,
        directory_name: str = "traces",
    ):
        self.directory_name = directory_name

    def _candidate_snapshot(
        self,
        candidate: dict,
    ) -> dict:
        """Create a serializable candidate-test snapshot."""

        code = candidate.get(
            "code",
            "",
        )

        return {
            "file_path": candidate.get(
                "file_path"
            ),
            "target_file": candidate.get(
                "target_file"
            ),
            "rationale": candidate.get(
                "rationale"
            ),
            "code": code,
            "code_sha256": _sha256_text(
                code
            ),
        }

    def _build_document(
        self,
        repository_path: Path,
        state: dict,
        session_id: str,
        created_at_utc: str,
    ) -> dict:
        """Build the structured trace document."""

        staged_diff = state.get(
            "staged_diff",
            "",
        )

        candidate_tests = [
            self._candidate_snapshot(
                candidate
            )
            for candidate
            in state.get(
                "candidate_tests",
                [],
            )
        ]

        return {
            "schema_version": 1,
            "session_id": session_id,
            "created_at_utc": created_at_utc,
            "repository_name": repository_path.name,

            "final_status": state.get(
                "status"
            ),

            "message": state.get(
                "message"
            ),

            "input": {
                "staged_files": state.get(
                    "staged_files",
                    [],
                ),
                "staged_diff_sha256": _sha256_text(
                    staged_diff
                ),
                "staged_diff_characters": len(
                    staged_diff
                ),
            },

            "analysis": {
                "risk_level": state.get(
                    "risk_level"
                ),
                "risky_files": state.get(
                    "risky_files",
                    [],
                ),
                "test_gaps": state.get(
                    "test_gaps",
                    [],
                ),
                "summary": state.get(
                    "analysis_summary"
                ),
            },

            "candidate_tests": candidate_tests,

            "execution": {
                "success": state.get(
                    "test_success"
                ),
                "exit_code": state.get(
                    "test_exit_code"
                ),
                "timed_out": state.get(
                    "test_timed_out"
                ),
                "stdout": _truncate_text(
                    state.get(
                        "test_stdout",
                        "",
                    )
                ),
                "stderr": _truncate_text(
                    state.get(
                        "test_stderr",
                        "",
                    )
                ),
            },

            "retry": {
                "count": state.get(
                    "retry_count",
                    0,
                ),
            },

            "approval": {
                "granted": state.get(
                    "approval_granted"
                ),
                "applied_files": state.get(
                    "applied_files",
                    [],
                ),
            },

            "events": state.get(
                "trace_events",
                [],
            ),
        }

    def write(
        self,
        repository_path: str,
        state: dict,
    ) -> str:
        """Write one execution trace to the repository traces folder."""

        repository_root = Path(
            repository_path
        ).resolve()

        trace_directory = (
            repository_root
            / self.directory_name
        )

        trace_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        now = datetime.now(
            timezone.utc
        )

        created_at_utc = (
            now.isoformat()
        )

        timestamp = now.strftime(
            "%Y%m%dT%H%M%S%fZ"
        )

        session_id = uuid4().hex

        trace_file = (
            trace_directory
            / (
                f"trace_{timestamp}_"
                f"{session_id[:8]}.json"
            )
        )

        document = self._build_document(
            repository_path=repository_root,
            state=state,
            session_id=session_id,
            created_at_utc=created_at_utc,
        )

        trace_file.write_text(
            json.dumps(
                document,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        return trace_file.relative_to(
            repository_root
        ).as_posix()