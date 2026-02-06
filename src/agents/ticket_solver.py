import logging
from pathlib import Path

from src.agents.base import extract_session_id, print_agent_message, run_agent_query
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
3. Git add ONLY the files that are part of the implementation (listed in the plan)

CRITICAL RULES FOR THIS PHASE:
- Follow the plan's file list and implementation steps
- Only modify/create files that are listed in the plan
- Maintain existing code style and patterns
- Add appropriate error handling and validation if needed
- DO NOT write new tests - a separate agent handles test writing if needed
- After making changes, use `git add` to stage ONLY the files listed in the plan
- DO NOT git add any temporary or helper files you created for your own use (e.g., JSON files
  describing violations, test scripts for debugging, analysis files, scratch files, etc.)
- If you create any temporary helper files, delete them before finishing

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

TEST_WRITER_PHASE_SYSTEM_PROMPT = """
You are an expert Software Engineer evaluating whether tests are needed for recent code changes.

CRITICAL: In MOST cases, new tests are NOT needed. Only add tests in these rare situations:
1. New complex or risky logic that doesn't have existing test coverage
2. Entirely new modules or components with no tests

DO NOT add tests for:
- Simple changes, bug fixes, or refactors
- Code that is already covered by existing tests
- Configuration changes
- Changes to existing well-tested code
- Minor feature additions to tested modules

Your role:
1. Review the staged changes (git diff --cached)
2. Check existing test coverage for the modified areas
3. ONLY if one of the rare situations above applies, write minimal focused tests
4. If you add tests, use `git add` to stage them

CRITICAL RULES:
- Default to NOT writing tests - most changes don't need them
- If existing tests cover the changes, do nothing
- If you write tests, keep them minimal and focused
- Follow existing test patterns in the codebase
- After writing tests, use `git add` to stage ONLY the test files you created
- DO NOT git add any temporary or helper files you created for your own use
- If you create any temporary helper files, delete them before finishing
"""

TEST_WRITER_PHASE_PROMPT_TEMPLATE = """
Review the staged changes and determine if new tests are truly needed.

Issue Key: {issue_key}
Summary: {summary}

Remember: Most changes do NOT need new tests. Only add tests for new complex/risky logic
without existing coverage, or entirely new modules.

Steps:
1. Run `git diff --cached` to see what was changed
2. Check if existing tests already cover these changes
3. Only if truly needed (rare), write minimal tests
4. Run `git add` to stage ONLY the test files you created
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
        if session_id is None:
            session_id = extract_session_id(message)
            if session_id:
                continue
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
        cwd=workspace_path,
        mcp_config_path=mcp_config_path,
        session_id=session_id,
    ):
        print_agent_message(message)


async def write_tests_if_needed(
    issue: JiraIssue,
    session_id: str,
    workspace_path: Path | None = None,
    mcp_config_path: Path | None = None,
) -> None:
    """
    Evaluate staged changes and add tests only if truly needed.

    Tests are only added in rare cases:
    - New complex/risky logic without existing test coverage
    - Entirely new modules or components
    """
    issue_context = {
        "issue_key": issue.key,
        "summary": issue.summary,
    }
    test_writer_prompt = TEST_WRITER_PHASE_PROMPT_TEMPLATE.format(**issue_context)

    async for message in run_agent_query(
        prompt=test_writer_prompt,
        system_prompt=TEST_WRITER_PHASE_SYSTEM_PROMPT,
        allowed_tools=["Glob", "Bash", "Read", "Grep", "Write"],
        cwd=workspace_path,
        mcp_config_path=mcp_config_path,
        session_id=session_id,
    ):
        print_agent_message(message)


async def try_solve_ticket(
    issue: JiraIssue,
    workspace_path: Path | None = None,
    mcp_config_path: Path | None = None,
    enable_test_writer: bool = True,
) -> str:
    """
    Solve a Jira ticket using a Plan-Act workflow with Claude Agent SDK.

    The workflow consists of phases:
    1. Planning Phase: Explore codebase and create PLAN.md with implementation details
    2. Execution Phase: Implement the plan
    3. Test Writing Phase (optional): Add tests only if truly needed (rare cases)

    Args:
        issue: The JiraIssue object containing all issue details
        workspace_path: Optional path to workspace root. Defaults to current directory.
        mcp_config_path: Optional path to mcp.json configuration file.
        enable_test_writer: Whether to run the test writer phase. Defaults to False.

    Returns:
        The session_id from the conversation
    """
    plan_path, session_id = await plan_ticket(issue, workspace_path, mcp_config_path)
    logger.info(
        "Plan file created at - %s. Now running the executor agent to implement it.", str(plan_path)
    )
    await execute_plan(issue, session_id, plan_path, workspace_path, mcp_config_path)
    if enable_test_writer:
        logger.info("Evaluating if new tests are needed for the changes.")
        await write_tests_if_needed(issue, session_id, workspace_path, mcp_config_path)
    return session_id
