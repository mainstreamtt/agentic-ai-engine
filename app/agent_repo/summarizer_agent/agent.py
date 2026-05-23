"""Summarizer agent – summarizes conversations and provides helpful overviews."""

from google.adk.agents import LlmAgent

from app import config
from app.agent_repo.summarizer_agent.prompt import SUMMARIZER_AGENT_INSTRUCTION


summarizer_agent = LlmAgent(
    name="summarizer_agent",
    model=config.DEFAULT_LLM_MODEL,
    description="Agent that summarizes conversations and provides helpful overviews.",
    instruction=SUMMARIZER_AGENT_INSTRUCTION,
)
