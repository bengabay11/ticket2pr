from pathlib import Path


class TicketToPRError(Exception):
    pass


class EnhancedGitError(TicketToPRError):
    pass


class GitWorkspacePathNotExistsError(EnhancedGitError):
    def __init__(self, repo_path: Path) -> None:
        super().__init__(f"Repository path does not exists locally - '{repo_path.resolve()}'")


class GitFetchCheckoutError(EnhancedGitError):
    def __init__(self) -> None:
        super().__init__("Failed to fetch and checkout branch")


class LocalBranchAlreadyExistsError(GitFetchCheckoutError):
    def __init__(self, branch_name: str) -> None:
        super().__init__()
        self.branch_name = branch_name
        self.args = (f"Local branch '{branch_name}' already exists",)


class GitPushError(EnhancedGitError):
    def __init__(self) -> None:
        super().__init__("Failed to commit and push changes")


class InvalidGitRepositoryError(EnhancedGitError):
    def __init__(self) -> None:
        super().__init__("Error: The directory provided is not a valid Git repository.")


class NoStagedChangesError(EnhancedGitError):
    pass


class ClientError(TicketToPRError):
    pass


class GithubClientError(ClientError):
    pass


class FetchGithubBranchError(GithubClientError):
    pass


class FetchGithubBranchUnknownError(FetchGithubBranchError):
    def __init__(self, branch_name: str):
        super().__init__(f"Failed to find base branch '{branch_name}': unknown error")


class GithubBranchNotFoundError(FetchGithubBranchError):
    def __init__(self, branch_name: str, repo_full_name: str):
        super().__init__(
            f"Failed to find base branch '{branch_name}' on repository: '{repo_full_name}'"
        )


class FetchGithubBranchServerError(FetchGithubBranchError):
    def __init__(self, branch_name: str, github_server_response: str):
        super().__init__(
            f"Failed to find base branch '{branch_name}'. Github server response: "
            f"{github_server_response}"
        )


class GithubBranchCreationError(GithubClientError):
    pass


class GithubBranchCreationServerError(GithubBranchCreationError):
    def __init__(self, branch_name: str, server_response: str):
        message = f"Error while created branch '{branch_name}': unknown server error."
        f"\n Server response: '{server_response}'"
        super().__init__(message)


class GithubBranchAlreadyExistsError(GithubBranchCreationError):
    def __init__(self, branch_name: str):
        message = f"Error while creating branch '{branch_name}': branch already exists"
        super().__init__(message)


class GithubPRCreationError(GithubClientError):
    def __init__(self) -> None:
        super().__init__("Failed to create pull request")


class GithubPRFetchError(GithubClientError):
    def __init__(self, pr_number: int):
        super().__init__(f"Failed to get pull request #{pr_number}")


class JiraClientError(ClientError):
    pass


class JiraIssueFetchError(JiraClientError):
    pass


class JiraIssueFetchUnknownError(JiraIssueFetchError):
    def __init__(self, issue_key: str):
        super().__init__(f"Unknown error occurred while fetched Jira issue {issue_key}")


class JiraIssueFetchServerError(JiraIssueFetchError):
    def __init__(self, issue_key: str, jira_api_response: str):
        super().__init__(
            f"Error occurred while fetched Jira issue {issue_key}. Jira server response: "
            f"{jira_api_response}"
        )


class JiraIssueNotFoundError(JiraIssueFetchError):
    def __init__(self, issue_key: str):
        super().__init__(
            f"Failed to fetch Jira issue {issue_key}: Issue does not exist or you do not have "
            "permission to see it."
        )


class PlanNotFoundError(TicketToPRError):
    def __init__(self, plan_path: Path):
        super().__init__(f"PLAN.md not found at {plan_path}.")


class PreCommitNotFoundError(TicketToPRError):
    def __init__(self) -> None:
        super().__init__("pre-commit executable not found in PATH.")


class AgentError(Exception):
    pass


class AgentQueryUnknownError(AgentError):
    def __init__(self, error_msg: str) -> None:
        super().__init__(
            f"Unknown error occurred while sending query to the agent. Error: {error_msg}"
        )


class AgentLowCreditBalanceError(AgentError):
    def __init__(self) -> None:
        super().__init__("Claude code agent sdk credit balance is too low")
