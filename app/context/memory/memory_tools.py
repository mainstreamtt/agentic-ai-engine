"""Memory tools for agents – wraps ADK memory operations as callable tools."""

from google.adk.tools.tool_context import ToolContext


async def memorize_session(tool_context: ToolContext) -> str:
    """Save the current conversation to long-term memory.

    Call this at the end of a meaningful exchange or whenever the user
    asks you to remember something. Key facts are extracted from the
    session and persisted so they can be recalled in future conversations.

    Returns:
        Confirmation string.
    """
    await tool_context.add_session_to_memory()
    return "Session saved to long-term memory."
