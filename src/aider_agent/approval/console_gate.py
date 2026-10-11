from difflib import unified_diff
from pathlib import Path, PurePosixPath


class ConsoleApprovalGate:
    """Interactive console approval gate for candidate tests."""

    def _candidate_destination(
        self,
        repository_path: str,
        file_path: str,
    ) -> Path:
        """Resolve the candidate path inside the repository."""

        relative_path = PurePosixPath(
            file_path.replace("\\", "/")
        )

        return (
            Path(repository_path)
            / Path(*relative_path.parts)
        )

    def _build_diff(
        self,
        repository_path: str,
        candidate: dict,
    ) -> str:
        """Build a unified diff for human review."""

        file_path = candidate[
            "file_path"
        ]

        destination = self._candidate_destination(
            repository_path,
            file_path,
        )

        if destination.exists():
            old_text = destination.read_text(
                encoding="utf-8"
            )

            old_name = (
                f"a/{file_path}"
            )

        else:
            old_text = ""
            old_name = "/dev/null"

        new_text = candidate[
            "code"
        ]

        diff_lines = unified_diff(
            old_text.splitlines(),
            new_text.splitlines(),
            fromfile=old_name,
            tofile=f"b/{file_path}",
            lineterm="",
        )

        diff = "\n".join(
            diff_lines
        )

        if not diff:
            return (
                "(No content changes.)"
            )

        return diff

    def _show_candidate_summary(
        self,
        candidate_tests: list[dict],
    ) -> None:
        """Display candidate information before approval."""

        print()
        print(
            "=== Candidate Tests Ready for Review ==="
        )

        for index, candidate in enumerate(
            candidate_tests,
            start=1,
        ):
            print()
            print(
                f"Candidate {index}"
            )
            print(
                "File:",
                candidate["file_path"],
            )
            print(
                "Target:",
                candidate["target_file"],
            )
            print(
                "Reason:",
                candidate["rationale"],
            )

    def _show_diffs(
        self,
        repository_path: str,
        candidate_tests: list[dict],
    ) -> None:
        """Display candidate diffs."""

        print()
        print(
            "=== Candidate Test Diff ==="
        )

        for candidate in candidate_tests:
            print()

            print(
                self._build_diff(
                    repository_path,
                    candidate,
                )
            )

    def request_approval(
        self,
        repository_path: str,
        candidate_tests: list[dict],
    ) -> bool:
        """Ask the human to approve or reject candidate tests."""

        if not candidate_tests:
            return False

        self._show_candidate_summary(
            candidate_tests
        )

        while True:
            print()

            decision = input(
                "[A] Approve  "
                "[R] Reject  "
                "[V] View Diff: "
            ).strip().lower()

            if decision == "a":
                return True

            if decision == "r":
                return False

            if decision == "v":
                self._show_diffs(
                    repository_path,
                    candidate_tests,
                )
                continue

            print(
                "Invalid choice. "
                "Enter A, R, or V."
            )