"""ADK tool functions for explicit session-state read/write.

Any LlmAgent that includes these tools can persist values across turns and
read them back — without relying on output_key prompt interpolation.

Usage in an agent:
    from app.context.state.state_tools import save_state, load_state, list_state_keys

    my_agent = LlmAgent(
        ...
        tools=[save_state, load_state, list_state_keys],
    )

The agent can then call them naturally:
    save_state(key="user_name", value="Alice")
    load_state(key="user_name")          → "Alice"
    list_state_keys()                    → "user_name, trip_details"
"""

import json

from google.adk.tools.tool_context import ToolContext


def save_state(key: str, value: str, tool_context: ToolContext) -> str:
    """Persist a string value in the session state under *key*.

    The value survives across turns and can be read back with load_state().
    To store structured data, serialize it to JSON first.

    Args:
        key:   State key (snake_case recommended, e.g. "user_name").
        value: String value to store. Use JSON for dicts / lists.

    Returns:
        Confirmation string.
    """
    tool_context.state[key] = value
    return f"Saved: {key} = {value!r}"


def load_state(key: str, tool_context: ToolContext) -> str:
    """Read a value previously saved with save_state().

    Args:
        key: State key to look up.

    Returns:
        The stored string value, or a "not found" message if absent.
    """
    value = tool_context.state.get(key)
    if value is None:
        return f"State key '{key}' not found."
    return str(value)


def list_state_keys(tool_context: ToolContext) -> str:
    """List all keys currently stored in the session state.

    Returns:
        Comma-separated key names, or "State is empty." if none exist.
    """
    keys = [k for k in tool_context.state if not k.startswith("_")]
    if not keys:
        return "State is empty."
    return ", ".join(sorted(keys))
