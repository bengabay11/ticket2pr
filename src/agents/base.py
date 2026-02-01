from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

from claude_agent_sdk import ClaudeAgentOptions, ContentBlock, query


async def run_agent_query(
    prompt: str,
    system_prompt: str,
    allowed_tools: list[str],
    permission_mode: str | None = None,
    cwd: Path | None = None,
    mcp_config_path: Path | None = None,
) -> AsyncGenerator[str | list[ContentBlock] | Any]:
    """
    Execute a Claude Agent SDK query with standardized message handling.

    This function encapsulates the common pattern of creating ClaudeAgentOptions,
    executing a query, and printing the results.

    Args:
        prompt: The user prompt to send to the agent
        system_prompt: The system prompt defining the agent's role and behavior
        allowed_tools: List of tool names the agent is allowed to use
        permission_mode: Optional permission mode (e.g., "acceptEdits").
                        If None, uses default permission handling.
        cwd: Optional current working directory for the agent to run from.
        mcp_config_path: Optional path to mcp.json configuration file for MCP servers.
    """
    options_kwargs = {
        "allowed_tools": allowed_tools,
        "system_prompt": system_prompt,
    }
    if permission_mode is not None:
        options_kwargs["permission_mode"] = permission_mode

    if cwd is not None:
        options_kwargs["cwd"] = str(cwd)

    if mcp_config_path is not None:
        options_kwargs["mcp_config_path"] = str(mcp_config_path)

    options = ClaudeAgentOptions(**options_kwargs)
    async for message in query(prompt=prompt, options=options):
        # TODO: handle balance too low gracefully
        # if isinstance(message, AssistantMessage):
        #     block = message.content[0]  # noqa: ERA001
        #     if isinstance(block, TextBlock) and block.text == "Credit balance is too low":
        #         raise AgentLowCreditBalanceError

        #     yield message.content
        if hasattr(message, "result") and message.result:
            yield message.result
        elif hasattr(message, "content") and message.content:
            yield message.content
