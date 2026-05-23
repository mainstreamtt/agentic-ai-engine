"""Summarizer Critic — standalone ADK LlmAgent exposed as an A2A server.

Receives a summary (and optionally the original text) and returns a structured
critique with per-criterion scores, strengths, improvement suggestions, and a
one-sentence verdict.
"""

import os

from google.adk.agents import LlmAgent

from .prompt import CRITIC_INSTRUCTION

MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash")

critic_agent = LlmAgent(
    name="summarizer_critic",
    model=MODEL,
    description=(
        "Evaluates the quality of a text summary and returns structured "
        "feedback: per-criterion scores (accuracy, completeness, clarity, "
        "conciseness, structure), strengths, actionable improvements, and a "
        "one-sentence verdict."
    ),
    instruction=CRITIC_INSTRUCTION,
)
