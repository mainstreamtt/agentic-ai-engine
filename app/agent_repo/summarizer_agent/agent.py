"""Summarizer agent – summarizes conversations and provides helpful overviews."""

import os

from google.adk.agents import LlmAgent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, SseConnectionParams

from google.adk.tools import preload_memory

from google.adk.tools import load_artifacts

from app import config
from app.agent_repo.summarizer_agent.prompt import SUMMARIZER_AGENT_INSTRUCTION
from app.context.artifacts.artifact_tools import save_artifact, list_artifacts
from app.context.memory.memory_tools import memorize_session
from app.context.rag.rag_tools import make_rag_retrieval_tool
from app.context.state.state_tools import save_state, load_state, list_state_keys

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

# Remote A2A critic — resolves its agent card from the running critic server.
# The card is fetched lazily on first use, so startup is not blocked even if
# the critic container is not yet running.
_critic_agent = RemoteA2aAgent(
    name="summarizer_critic",
    agent_card=config.CRITIC_A2A_URL,
    description=(
        "Evaluates the quality of a summary and returns structured feedback: "
        "per-criterion scores, strengths, improvements, and a verdict."
    ),
)

_rag_tool = make_rag_retrieval_tool()

summarizer_agent = LlmAgent(
    name="summarizer_agent",
    model=config.DEFAULT_LLM_MODEL,
    description="Agent that summarizes conversations and provides helpful overviews.",
    instruction=SUMMARIZER_AGENT_INSTRUCTION,
    tools=[
        _fetch_url_toolset,
        AgentTool(agent=_search_agent),
        AgentTool(agent=_critic_agent),
        save_state,
        load_state,
        list_state_keys,
        memorize_session,
        preload_memory,
        save_artifact,
        list_artifacts,
        load_artifacts,
        *([_rag_tool] if _rag_tool else []),
    ],
)
