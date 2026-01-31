import os
from pathlib import Path

from src.agents.base import run_agent_query
from src.clients.jira_client import JiraIssue
from src.exceptions import PlanNotFoundError

PLANNING_PHASE_SYSTEM_PROMPT = """
You are an expert Software Engineer in the PLANNING phase of implementing a Jira ticket.

Your role in this phase is to:
1. Read and understand the Jira ticket requirements thoroughly
2. Explore the codebase structure to understand the project layout
3. Identify relevant files, modules, and existing patterns
4. Understand dependencies and relationships between components
5. Note any existing tests and testing patterns
6. Create a comprehensive PLAN.md file that details:
   - Overview of the changes needed
   - List of files that will be modified (with paths)
   - List of files that will be created (with paths)
   - Step-by-step implementation approach
   - Testing strategy
   - Any risks or considerations

CRITICAL RULES FOR THIS PHASE:
- You can ONLY write to PLAN.md file (use Write tool)
- DO NOT modify any other files
- Use Read, Glob, Grep, and Bash to explore the codebase first
- The plan must be detailed and specific
- Include exact file paths that will be touched
- Break down the implementation into clear, sequential steps
- Consider edge cases and error handling in your plan

The PLAN.md should be comprehensive enough that another engineer could implement it.

Start by exploring the codebase, then write the PLAN.md file. Be specific about file
paths and implementation details.
"""

PLANNING_PHASE_PROMPT_TEMPLATE = """
Please explore the codebase and create PLAN.md for this ticket.

Issue Key: {issue_key}
Issue Type: {issue_type}
Status: {status}
Summary: {summary}
URL: {url}

Description:
{description}
"""

EXECUTION_PHASE_SYSTEM_PROMPT = """
You are an expert Software Engineer in the EXECUTION phase of implementing a Jira ticket.

Your role in this phase is to implement the plan:
1. Read the PLAN.md file that was created in the Planning Phase
2. Follow the plan step-by-step to implement the solution
3. Make the necessary code changes
4. Run relevant tests to verify the implementation
5. Fix any issues that arise during testing
6. Git add all relevant files that were changed or created

CRITICAL RULES FOR THIS PHASE:
- Read PLAN.md first to understand what needs to be done
- Follow the plan's file list and implementation steps
- Only modify/create files that are listed in the plan
- Maintain existing code style and patterns
- Add appropriate error handling and validation
- Run tests after implementation
- If tests fail, analyze and fix the issues
- After making changes, use `git add` to stage all files that were modified or created

You have full access to modify files, but stay within the scope of the plan.

Start by reading PLAN.md, then proceed with the implementation.
"""

EXECUTION_PHASE_PROMPT_TEMPLATE = """
Please implement the solution according to PLAN.md for this ticket.

Issue Key: {issue_key}
Issue Type: {issue_type}
Status: {status}
Summary: {summary}
URL: {url}

Description:
{description}
"""


async def plan_ticket(issue: JiraIssue, workspace_path: Path | None = None) -> Path:
    """
    Plan the implementation for a Jira ticket by exploring the codebase and creating PLAN.md.

    Args:
        issue: The JiraIssue object containing all issue details
        workspace_path: Optional path to workspace root. Defaults to current directory.

    Returns:
        Path to the created PLAN.md file

    Raises:
        FileNotFoundError: If PLAN.md was not created after planning
    """
    final_workspace_path = workspace_path.expanduser() if workspace_path else Path.cwd()
    plan_path = final_workspace_path / "PLAN.md"
    issue_context = {
        "issue_key": issue.key,
        "issue_type": issue.type or "Unknown",
        "status": issue.status or "Unknown",
        "summary": issue.summary,
        "url": issue.url,
        "description": issue.description or "No description provided",
    }

    planning_prompt = PLANNING_PHASE_PROMPT_TEMPLATE.format(**issue_context)

    async for message in run_agent_query(
        prompt=planning_prompt,
        system_prompt=PLANNING_PHASE_SYSTEM_PROMPT,
        allowed_tools=["Glob", "Bash", "Read", "Grep", "Write"],  # Can write PLAN.md
    ):
        print(message)

    if not plan_path.exists():
        raise PlanNotFoundError(plan_path)

    return plan_path


async def execute_plan(
    issue: JiraIssue, plan_path: Path | None = None, workspace_path: Path | None = None
) -> None:
    """
    Execute the implementation plan for a Jira ticket according to PLAN.md.

    Args:
        issue: The JiraIssue object containing all issue details
        plan_path: Optional path to PLAN.md file.
                   If not provided, looks for PLAN.md in workspace_path.
        workspace_path: Optional path to workspace root. Defaults to current directory.
    """
    final_workspace_path = workspace_path.expanduser() if workspace_path else Path.cwd()

    if plan_path is None:
        plan_path = final_workspace_path / "PLAN.md"

    if not plan_path.exists():
        raise PlanNotFoundError(plan_path)

    # Format prompts with issue details
    issue_context = {
        "issue_key": issue.key,
        "issue_type": issue.type or "Unknown",
        "status": issue.status or "Unknown",
        "summary": issue.summary,
        "url": issue.url,
        "description": issue.description or "No description provided",
    }
    execution_prompt = EXECUTION_PHASE_PROMPT_TEMPLATE.format(**issue_context)

    async for message in run_agent_query(
        prompt=execution_prompt,
        system_prompt=EXECUTION_PHASE_SYSTEM_PROMPT,
        allowed_tools=["Glob", "Bash", "Read", "Grep", "Write"],  # Full access
        permission_mode="acceptEdits",  # Auto-approve edits without asking
    ):
        print(message)


async def try_solve_ticket(issue: JiraIssue, workspace_path: Path | None = None) -> None:
    """
    Solve a Jira ticket using a Plan-Act workflow with Claude Agent SDK.

    The workflow consists of two phases:
    1. Planning Phase: Explore codebase and create PLAN.md with implementation details
    2. Execution Phase: Implement the plan and run tests

    Args:
        issue: The JiraIssue object containing all issue details
        workspace_path: Optional path to workspace root. Defaults to current directory.
    """
    plan_path = await plan_ticket(issue, workspace_path)
    await execute_plan(issue, plan_path, workspace_path)
