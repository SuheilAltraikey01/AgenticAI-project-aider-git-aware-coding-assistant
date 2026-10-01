from pathlib import Path

from git import InvalidGitRepositoryError, NoSuchPathError, Repo


class GitDiffReader:
    """Read staged changes from a local Git repository."""

    def __init__(self, repository_path: str | Path = "."):
        """
        Create a reader for a Git repository.

        Args:
            repository_path:
                Path to the local Git repository.
        """
        self.repository_path = Path(repository_path)

    def _get_repository(self) -> Repo:
        """Open and validate the configured Git repository."""
        try:
            return Repo(self.repository_path)
        except (InvalidGitRepositoryError, NoSuchPathError) as exc:
            raise ValueError(
                f"Not a valid Git repository: {self.repository_path}"
            ) from exc

    def get_staged_diff(self) -> str:
        """
        Return the staged Git diff.

        This reads changes that have already been added to the Git index
        using 'git add'. The method does not modify the repository.
        """
        repo = self._get_repository()

        return repo.git.diff(
            "--cached",
            "--no-color",
        )

    def get_staged_files(self) -> list[str]:
        """
        Return the names of files currently staged for commit.
        """
        repo = self._get_repository()

        output = repo.git.diff(
            "--cached",
            "--name-only",
        )

        if not output.strip():
            return []

        return [
            line.strip()
            for line in output.splitlines()
            if line.strip()
        ]