"""Artifact tools for agents – save and list GCS-backed artifacts.

Supported formats:
  - Markdown  (.md)  – stored as text/markdown
  - PDF       (.pdf) – text converted to a PDF via fpdf2

Usage in an agent:
    from app.context.artifacts.artifact_tools import save_artifact, list_artifacts

    my_agent = LlmAgent(
        ...
        tools=[save_artifact, list_artifacts],
    )
"""

from __future__ import annotations

import structlog
from fpdf import FPDF
from google.adk.tools.tool_context import ToolContext
from google.genai import types

logger = structlog.get_logger(__name__)


def _text_to_pdf_bytes(content: str) -> bytes:
    """Render *content* as a plain-text PDF and return the raw bytes."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)
    # multi_cell handles line wrapping and newlines
    pdf.multi_cell(0, 6, text=content)
    return bytes(pdf.output())


async def save_artifact(
    filename: str,
    content: str,
    tool_context: ToolContext,
) -> str:
    """Save *content* as a GCS artifact.

    The format is determined by the file extension:
      - ``.md``  → saved as Markdown text (text/markdown)
      - ``.pdf`` → content is rendered into a PDF document (application/pdf)

    Args:
        filename: Target filename, e.g. ``"summary.md"`` or ``"report.pdf"``.
        content:  Text content to save (Markdown source for both formats).

    Returns:
        Confirmation string with the saved filename and version number.
    """
    filename = filename.strip()
    # Strip any existing user: prefix so we don't double-apply it
    if filename.startswith("user:"):
        filename = filename[5:]

    if filename.endswith(".pdf"):
        pdf_bytes = _text_to_pdf_bytes(content)
        part = types.Part(
            inline_data=types.Blob(
                mime_type="application/pdf",
                data=pdf_bytes,
            )
        )
    else:
        # Default to Markdown for .md and any other text-based extension
        if not filename.endswith(".md"):
            filename += ".md"
        part = types.Part(text=content)

    # Prefix with "user:" so GCS stores under {app}/{user}/user/ instead of
    # {app}/{user}/{session_id}/ — artifacts persist across sessions.
    user_filename = f"user:{filename}"
    version = await tool_context.save_artifact(filename=user_filename, artifact=part)
    logger.info("Artifact saved", filename=user_filename, version=version)
    return f"Saved artifact '{filename}' (version {version})."


async def list_artifacts(tool_context: ToolContext) -> str:
    """List all artifact filenames saved for this user.

    Returns:
        Comma-separated filenames, or a message if none exist.
    """
    names = await tool_context.list_artifacts()
    # Strip the internal user: prefix before showing names to the agent
    display_names = [n[5:] if n.startswith("user:") else n for n in names]
    if not display_names:
        return "No artifacts saved yet."
    return ", ".join(display_names)
