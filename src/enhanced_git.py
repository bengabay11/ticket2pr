from pathlib import Path

import git
from typing_extensions import Self

from src.exceptions import (
    GitCloneError,
    GitFetchCheckoutUnknownError,
    GitPushError,
    GitWorkspacePathNotExistsError,
    LocalBranchAlreadyExistsError,
    NoStagedChangesError,
)


class EnhancedGit:
    """
    An enhanced Git wrapper that combines multiple git operations into single method calls.

    This class provides high-level methods that perform common git workflows by executing
    multiple underlying git commands in sequence.
    """

    def __init__(self, repo_path: Path = Path(".")) -> None:
        """
        Initialize an EnhancedGit instance for a given repository path.

        Args:
            repo_path: Path to the git repository (default: current directory)
        """
        if not repo_path.exists():
            raise GitWorkspacePathNotExistsError(repo_path)
        self.repo_path = repo_path.expanduser()
        self._repo = None

    @classmethod
    def clone_repo(cls, clone_url: str, target_path: Path) -> Self:
        """
        Clone a repository to the specified path and return an EnhancedGit instance.

        Args:
            clone_url: The URL of the repository to clone
            target_path: The path where the repository will be cloned

        Returns:
            An EnhancedGit instance for the cloned repository

        Raises:
            GitCloneError: If cloning fails
        """
        try:
            git.Repo.clone_from(clone_url, target_path)
        except Exception as e:
            raise GitCloneError(clone_url, str(e)) from e
        return cls(target_path)

    @property
    def repo(self) -> git.Repo:
        """Lazy-load the git repository."""
        if self._repo is None:
            self._repo = git.Repo(self.repo_path)
        return self._repo

    def fetch_and_checkout_branch(self, branch_name: str) -> None:
        """
        Combined operation: Fetch from origin and checkout the specified branch.

        This method performs multiple git operations in sequence:
        1. Fetches the latest changes from origin
        2. Checks out the branch (switches if local, creates tracking branch if remote-only)

        Args:
            branch_name: Name of the branch to checkout

        Raises:
            LocalBranchAlreadyExistsError: If the branch already exists locally
            GitFetchCheckoutError: If a git error occurs
        """
        if branch_name in self.repo.heads:
            raise LocalBranchAlreadyExistsError(branch_name)

        try:
            origin = self.repo.remotes.origin
            origin.fetch()
            self.repo.git.checkout(branch_name)
        except Exception as e:
            raise GitFetchCheckoutUnknownError(str(e)) from e

    def add_all_changes(self) -> None:
        """
        Add all changes to the staging area.
        """
        self.repo.git.add(A=True)

    def commit_and_push(
        self, message: str, remote: str = "origin", no_verify: bool = False
    ) -> git.Commit | None:
        """
        Combined operation: Stage all changes, commit, and push to remote.

        This method performs multiple git operations in sequence:
        1. Checks if there are any changes to commit
        2. Stages all changes (including untracked files)
        3. Creates a commit with the provided message
        4. Pushes the commit to the remote repository

        Args:
            message: Commit message
            remote: Remote name to push to (default: "origin")
            no_verify: If True, bypasses pre-commit hooks with --no-verify (default: False)

        Returns:
            The created commit, or None if there were no changes

        Raises:
            Exception: If the directory is not a valid git repository or if push fails
        """
        try:
            # Check if there are any changes to commit
            if not self.repo.is_dirty(untracked_files=True):
                print("No changes detected. Nothing to commit.")
                return None

            if no_verify:
                commit = self.repo.git.commit("-m", message, "--no-verify")
                commit = self.repo.head.commit
            else:
                commit = self.repo.index.commit(message)

            # Push to remote
            remote_obj = self.repo.remote(name=remote)
            current_branch = self.repo.active_branch.name
            remote_obj.push(current_branch)
        except Exception as e:
            raise GitPushError from e
        else:
            return commit

    def get_staged_changes(self) -> tuple[str, list[str]]:
        """
        Get staged changes and list of changed files.

        Returns:
            A tuple containing:
            - staged_diff: The diff of staged changes
            - changed_file_paths: List of file paths that have been changed

        Raises:
            Exception: If no changes are staged
        """
        staged_diff = self.repo.git.diff("--staged")
        if not staged_diff:
            raise NoStagedChangesError

        changed_file_paths = [item.a_path for item in self.repo.index.diff("HEAD")]

        return staged_diff, changed_file_paths
