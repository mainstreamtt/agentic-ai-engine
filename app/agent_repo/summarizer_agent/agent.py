"""Summarizer agent – summarizes conversations and provides helpful overviews."""

import os

from google.adk.agents import LlmAgent
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, SseConnectionParams

from app import config
from app.agent_repo.summarizer_agent.prompt import SUMMARIZER_AGENT_INSTRUCTION

# URL of the fetch-url MCP server (overridable via environment variable)
_MCP_SERVER_URL = os.getenv("FETCH_URL_MCP_SERVER", "http://localhost:3001/sse")

_fetch_url_toolset = McpToolset(
    connection_params=SseConnectionParams(url=_MCP_SERVER_URL),
    tool_filter=["fetch_url"],
)

# Wrap google_search in a sub-agent so it becomes a regular custom tool call.
# Gemini forbids mixing its built-in grounding tool with custom/MCP tools, but
# an AgentTool is just a function call from the parent agent's perspective.
_search_agent = LlmAgent(
    name="search_agent",
    model=config.DEFAULT_LLM_MODEL,
    description="Searches the web using Google Search.",
    instruction="Use google_search to answer the query as concisely as possible.",
    tools=[google_search],
)

summarizer_agent = LlmAgent(
    name="summarizer_agent",
    model=config.DEFAULT_LLM_MODEL,
    description="Agent that summarizes conversations and provides helpful overviews.",
    instruction=SUMMARIZER_AGENT_INSTRUCTION,
    tools=[_fetch_url_toolset, AgentTool(agent=_search_agent)],
)
