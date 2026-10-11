from pathlib import Path, PurePosixPath


class CandidateTestApplier:
    """
    Apply human-approved candidate tests to the real repository.

    This class does not stage, commit, or push Git changes.
    """

    def _validate_candidate_path(
        self,
        file_path: str,
    ) -> PurePosixPath:
        """Validate that the destination stays inside tests/."""

        path = PurePosixPath(
            file_path.replace("\\", "/")
        )

        if path.is_absolute():
            raise ValueError(
                "Candidate test path must be relative."
            )

        if ".." in path.parts:
            raise ValueError(
                "Candidate test path cannot contain '..'."
            )

        if (
            not path.parts
            or path.parts[0] != "tests"
        ):
            raise ValueError(
                "Candidate test path must be inside tests/."
            )

        if path.suffix != ".py":
            raise ValueError(
                "Candidate test file must be a Python file."
            )

        return path

    def apply(
        self,
        repository_path: str,
        candidate_tests: list[dict],
    ) -> list[str]:
        """Write approved candidate tests into the real repository."""

        if not candidate_tests:
            raise ValueError(
                "At least one approved candidate test is required."
            )

        repository_root = Path(
            repository_path
        ).resolve()

        prepared_files = []

        # Validate every candidate before writing anything.
        for candidate in candidate_tests:
            relative_path = (
                self._validate_candidate_path(
                    candidate["file_path"]
                )
            )

            destination = (
                repository_root
                / Path(*relative_path.parts)
            ).resolve()

            try:
                destination.relative_to(
                    repository_root
                )

            except ValueError as exc:
                raise ValueError(
                    "Candidate path escapes the repository."
                ) from exc

            prepared_files.append(
                (
                    destination,
                    relative_path.as_posix(),
                    candidate["code"],
                )
            )

        applied_files = []

        for (
            destination,
            relative_path,
            code,
        ) in prepared_files:

            destination.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            destination.write_text(
                code,
                encoding="utf-8",
            )

            applied_files.append(
                relative_path
            )

        return applied_files