# Ticket2PR

Ticket2PR is an AI-powered automation tool designed to streamline the process of converting development tickets into ready-to-merge pull requests.

## Workflow

The tool runs a single pipeline from Jira ticket to GitHub PR. **Only the steps that truly need AI use it**—everything else is done with APIs and deterministic logic. That keeps token usage and run time low.

**Full pipeline:**

1. **Workspace** — If no workspace path is set (CLI or config), clone the repo to a temp folder; otherwise use the given path. The temp folder is removed when the run finishes.
2. **Fetch Jira issue** — Get ticket details via Jira API.
3. **Create branch** — Generate branch name from issue key/summary, create it on GitHub, and link the branch to the Jira ticket.
4. **Checkout branch** — Git fetch and checkout.
5. **Solve ticket** — **2 AI agents in sequence:** a **Planner** explores the codebase and writes a `PLAN.md` (no other files); an **Executor** implements that plan (code edits, then stages the changed files).
6. **Fix tests** _(optional, `--fix-tests`)_ — **2 AI agents in sequence:** a **Test planner** analyzes staged changes, finds existing related **tests**, and writes a `TESTS_PLAN.md`; a **Test fixer** runs those tests, fixes failures, and stages only the fix-related changes.
7. **Pre-commit** _(if installed and config present)_ — Run pre-commit; **only if it fails**, an **AI agent** tries to fix lint/format issues (with retries). This step is skipped if pre-commit isn’t installed or if `.pre-commit-config.yaml` is missing or not a file.
8. **Commit message & PR body** — **AI agent:** generates a conventional commit message and PR description from the changes and ticket context.
9. **Commit and push** — Git commit and push.
10. **PR title** — Build title from issue key and summary, e.g. `[PROJ-123] Summary`.
11. **Create PR** — Open the pull request via GitHub API.

## Agents

Ticket2PR uses **several specialized agents**, each with a single responsibility:

| Agent                     | Purpose                                                                                                                                               |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Planner**               | Reads the Jira ticket, explores the codebase, and writes a single `PLAN.md` with implementation steps and file list. Does not modify any other files. |
| **Executor**              | Implements the plan: makes the code changes and stages only the files listed in the plan.                                                             |
| **Test planner**          | Analyzes staged changes, finds existing related tests, and writes a `TESTS_PLAN.md` with test paths and run commands (used only with `--fix-tests`).  |
| **Test fixer**            | Runs tests from the plan, diagnoses failures, and applies fixes until all tests pass (used only with `--fix-tests`).                                  |
| **Pre-commit fixer**      | When pre-commit fails (lint/format, etc.), suggests and applies fixes so hooks pass.                                                                  |
| **Commit & PR generator** | Writes a conventional commit message and the PR body from the diff and ticket context.                                                                |

They run in sequence where needed; the workflow invokes only the agents required for the current run (e.g. no test fixer without `--fix-tests`, no pre-commit fixer if hooks pass or pre-commit isn’t available).

## Getting Started

Follow these steps to set up and start using Ticket2PR:

### Installation

You can install `ticket2pr` directly from PyPI:

```sh
pip install ticket2pr
```

### Usage

Run the Ticket2PR CLI to create a pull request from a Jira ticket:

```sh
ticket2pr run <JIRA_ISSUE_KEY>
```

Replace `<JIRA_ISSUE_KEY>` with the actual ID of your Jira ticket (e.g., `PROJ-123`).

Use `--fix-tests` (or `-t`) to run an extra step after solving the ticket: the tool will plan and run tests from the staged changes, fix any failures with an AI agent, and stage only the fix-related changes before committing.

### Configuration

Ticket2PR automatically guides you through the initial configuration process the first time you run the CLI.

To re-initialize the interactive configuration session, run:

```sh
ticket2pr init
```

Alternatively, you can manually configure settings by editing the `~/.ticket2pr/config.toml` file or by setting environment variables.

## Prerequisites

- **Jira Account and API Token:** An account with access to a Jira instance and a valid API token with necessary permissions to view tickets.
- **GitHub Account and Personal Access Token:** A GitHub account with permissions to create branches and pull requests in your target repository, and a [Personal Access Token (PAT)](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token) with `repo` scope for GitHub API access.
- **Claude Code:** Be logged in locally to Claude Code (used for the AI-powered steps).

## License

This project is open-sourced under the terms of the [LICENSE](LICENSE).
