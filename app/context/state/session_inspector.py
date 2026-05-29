"""Session inspector — structured logging and reporting for ADK sessions.

Provides three public functions:

    log_session_state(session)   – emit a structlog INFO with every state key/value
    log_session_events(session)  – emit a structlog INFO for each event in history
    format_session_report(session) – return a human-readable Markdown report string
"""

from __future__ import annotations

import json
from typing import Any

import structlog
from google.adk.sessions import Session

logger = structlog.get_logger(__name__)

# Keys written by ADK internals that clutter the output
_INTERNAL_PREFIXES = ("_", "a2a:")


def _is_user_key(key: str) -> bool:
    return not any(key.startswith(p) for p in _INTERNAL_PREFIXES)


def _truncate(value: Any, max_chars: int = 200) -> str:
    """Return a short string representation of *value*."""
    text = str(value)
    if len(text) > max_chars:
        return text[:max_chars] + f"… [{len(text) - max_chars} chars truncated]"
    return text


def log_session_state(session: Session) -> None:
    """Emit a structured log line for each user-visible session state key."""
    user_state = {k: v for k, v in session.state.items() if _is_user_key(k)}

    if not user_state:
        logger.info("session_state is empty", session_id=session.id)
        return

    logger.info(
        "session_state snapshot",
        session_id=session.id,
        key_count=len(user_state),
        keys=sorted(user_state.keys()),
    )
    for key, value in sorted(user_state.items()):
        logger.info(
            "  state",
            key=key,
            value=_truncate(value),
            type=type(value).__name__,
        )


def log_session_events(session: Session, *, max_events: int = 20) -> None:
    """Emit a structured log line for each event in the session history."""
    events = session.events[-max_events:]
    logger.info(
        "session_events",
        session_id=session.id,
        total_events=len(session.events),
        showing=len(events),
    )
    for i, event in enumerate(events):
        text = ""
        if event.content and event.content.parts:
            text = "".join(p.text for p in event.content.parts if p.text)

        func_calls = []
        func_responses = []
        if event.content and event.content.parts:
            for p in event.content.parts:
                if p.function_call:
                    func_calls.append(p.function_call.name)
                if p.function_response:
                    func_responses.append(p.function_response.name)

        logger.info(
            "  event",
            index=i,
            author=event.author or "?",
            is_final=event.is_final_response(),
            text_preview=_truncate(text, 120) if text else None,
            function_calls=func_calls or None,
            function_responses=func_responses or None,
        )


def format_session_report(session: Session) -> str:
    """Return a Markdown-formatted string summarising the session.

    Suitable for sending to the WebSocket client or printing to the console.
    """
    lines: list[str] = []

    # ── Header ──────────────────────────────────────────────────────────────
    lines.append(f"## Session Report")
    lines.append(f"- **ID**: `{session.id}`")
    lines.append(f"- **App**: `{session.app_name}`")
    lines.append(f"- **User**: `{session.user_id}`")
    lines.append(f"- **Events**: {len(session.events)}")
    lines.append("")

    # ── State ───────────────────────────────────────────────────────────────
    user_state = {k: v for k, v in session.state.items() if _is_user_key(k)}
    lines.append("### State Variables")
    if user_state:
        for key in sorted(user_state):
            lines.append(f"- **{key}**: {_truncate(user_state[key])}")
    else:
        lines.append("_(empty)_")
    lines.append("")

    # ── Event history ────────────────────────────────────────────────────────
    lines.append("### Event History")
    for i, event in enumerate(session.events):
        text = ""
        if event.content and event.content.parts:
            text = "".join(p.text for p in event.content.parts if p.text)

        func_calls = [
            p.function_call.name
            for p in (event.content.parts if event.content else [])
            if p.function_call
        ]
        func_responses = [
            p.function_response.name
            for p in (event.content.parts if event.content else [])
            if p.function_response
        ]

        badge = "✅" if event.is_final_response() else "🔄"
        author = event.author or "?"

        if func_calls:
            lines.append(f"{i}. {badge} **{author}** → tool call: `{'`, `'.join(func_calls)}`")
        elif func_responses:
            lines.append(f"{i}. {badge} **{author}** ← tool result: `{'`, `'.join(func_responses)}`")
        elif text:
            lines.append(f"{i}. {badge} **{author}**: {_truncate(text, 120)}")
        else:
            lines.append(f"{i}. {badge} **{author}**: _(no text)_")

    return "\n".join(lines)
