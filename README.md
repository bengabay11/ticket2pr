# Ticket2PR

Ticket2PR is an AI-powered automation tool designed to streamline the process of converting development tickets into ready-to-merge pull requests. It integrates with Jira and GitHub to automate tasks such as branch creation, commit message generation, code linting fixes, and pull request content generation, significantly reducing manual effort and accelerating development workflows.

## What's Included

Ticket2PR provides a comprehensive set of features to automate your development workflow:

- **🚀 Automated Workflow:** Orchestrates the entire process from ticket to pull request, handling branch creation, commit message generation, and PR content.
- **🤖 AI-Powered Agents:** Utilizes specialized agents for tasks like crafting intelligent commit messages, automatically fixing pre-commit issues, and assisting with ticket resolution.
- **🔗 Jira Integration:** Connects with Jira to fetch ticket details, enabling context-aware automation.
- **🐙 GitHub Integration:** Interacts with GitHub for branch management, pull request creation, and status updates.

## Prerequisites

- **Jira Account and API Token:** An account with access to a Jira instance and a valid API token with necessary permissions to view tickets.
- **GitHub Account and Personal Access Token:** A GitHub account with permissions to create branches and pull requests in your target repository, and a [Personal Access Token (PAT)](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token) with `repo` scope for GitHub API access.
- **Claude Code API Token:** Obtain an API token for Claude Code for AI-powered code assistance.

## Getting Started

Follow these steps to set up and start using Ticket2PR:

### Installation

You can install `ticket2pr` directly from PyPI:

```sh
pip install ticket2pr
```

### Configuration

Ticket2PR automatically guides you through the initial configuration process the first time you run the CLI.

To re-initialize the interactive configuration session, run:

```sh
ticket2pr init
```

Alternatively, you can manually configure settings by editing the `~/.ticket2pr/config.toml` file or by setting environment variables.

### Usage

Run the Ticket2PR CLI to create a pull request from a Jira ticket:

```sh
ticket2pr run <JIRA_ISSUE_KEY>
```

Replace `<JIRA_ISSUE_KEY>` with the actual ID of your Jira ticket (e.g., `PROJ-123`).

## License

This project is open-sourced under the terms of the [LICENSE](LICENSE).
