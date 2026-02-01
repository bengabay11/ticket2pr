import logging
from pathlib import Path

from src.agents.base import print_agent_message, run_agent_query
from src.clients.jira_client import JiraIssue
from src.exceptions import PlanNotFoundError

logger = logging.getLogger(__name__)

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
- DO NOT add PLAN.md to git (no git add commands)
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

Your role in this phase is to implement the plan provided in the prompt:
1. Follow the plan step-by-step to implement the solution
2. Make the necessary code changes
3. Git add all relevant files that were changed or created

CRITICAL RULES FOR THIS PHASE:
- Follow the plan's file list and implementation steps
- Only modify/create files that are listed in the plan
- Maintain existing code style and patterns
- Add appropriate error handling and validation if needed
- After making changes, use `git add` to stage all files that were modified or created

You have full access to modify files, but stay within the scope of the plan.
"""

EXECUTION_PHASE_PROMPT_TEMPLATE = """
Please implement the solution according to the plan below for this ticket.

Issue Key: {issue_key}
Issue Type: {issue_type}
Status: {status}
Summary: {summary}
URL: {url}

Description:
{description}

Plan:
{plan_content}
"""


async def plan_ticket(
    issue: JiraIssue, workspace_path: Path | None = None, mcp_config_path: Path | None = None
) -> tuple[Path, str]:
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

    session_id = None
    async for message in run_agent_query(
        prompt=planning_prompt,
        system_prompt=PLANNING_PHASE_SYSTEM_PROMPT,
        allowed_tools=["Glob", "Bash", "Read", "Grep", "Write"],  # Can write PLAN.md
        cwd=workspace_path,
        mcp_config_path=mcp_config_path,
    ):
        # First message is the session ID
        if session_id is None:
            session_id = message
        else:
            print_agent_message(message)

    if not plan_path.exists():
        raise PlanNotFoundError(plan_path)

    return plan_path, str(session_id)


async def execute_plan(
    issue: JiraIssue,
    session_id: str,
    plan_path: Path,
    workspace_path: Path | None = None,
    mcp_config_path: Path | None = None,
) -> None:
    if not plan_path.exists():
        raise PlanNotFoundError(plan_path)

    # Read plan content and delete the file to prevent accidental git add
    plan_content = plan_path.read_text()
    plan_path.unlink()

    issue_context = {
        "issue_key": issue.key,
        "issue_type": issue.type or "Unknown",
        "status": issue.status or "Unknown",
        "summary": issue.summary,
        "url": issue.url,
        "description": issue.description or "No description provided",
        "plan_content": plan_content,
    }
    execution_prompt = EXECUTION_PHASE_PROMPT_TEMPLATE.format(**issue_context)

    async for message in run_agent_query(
        prompt=execution_prompt,
        system_prompt=EXECUTION_PHASE_SYSTEM_PROMPT,
        allowed_tools=["Glob", "Bash", "Read", "Grep", "Write"],  # Full access
        permission_mode="acceptEdits",  # Auto-approve edits without asking
        cwd=workspace_path,
        mcp_config_path=mcp_config_path,
        session_id=session_id,
    ):
        print_agent_message(message)


async def try_solve_ticket(
    issue: JiraIssue, workspace_path: Path | None = None, mcp_config_path: Path | None = None
) -> str:
    """
    Solve a Jira ticket using a Plan-Act workflow with Claude Agent SDK.

    The workflow consists of two phases:
    1. Planning Phase: Explore codebase and create PLAN.md with implementation details
    2. Execution Phase: Implement the plan and run tests

    Args:
        issue: The JiraIssue object containing all issue details
        workspace_path: Optional path to workspace root. Defaults to current directory.
        mcp_config_path: Optional path to mcp.json configuration file.

    Returns:
        The session_id from the conversation
    """
    plan_path, session_id = await plan_ticket(issue, workspace_path, mcp_config_path)
    logger.info(
        "Plan file created at - %s. Now running the executor agent to implement it.", str(plan_path)
    )
    await execute_plan(issue, session_id, plan_path, workspace_path, mcp_config_path)
    return session_id
