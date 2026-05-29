"""Trip Planner — graph-based agent pipeline (ADK v2).

Graph topology (DAG with refinement loop):

  Customer
     │
     ▼
  triage_orchestrator          LlmAgent   — collects trip details → session state
     │
     ▼
  research_fan_out             ParallelAgent — true parallel fan-out
  ├── destination_researcher   LlmAgent   — fetch_url MCP
  ├── flight_hotel_scout       LlmAgent   — google_search
  └── budget_pre_assessor      LlmAgent   — no tools
     │  (all write to session state via output_key)
     ▼
  refinement_loop              LoopAgent  — iterative revision cycle (max 2)
  ├── itinerary_builder        LlmAgent   — fan-in: reads all 3 research keys
  └── quality_reviewer         LlmAgent   — APPROVED / NEEDS_REVISION / NEEDS_HUMAN
     │
     ▼
  response_router              LlmAgent   — conditional routing
  ├── final_response_agent     LlmAgent   — Approved / best-effort draft path
  └── human_handoff_agent      LlmAgent   — Needs human path

The root is a SequentialAgent that drives all stages in order.
Session state (output_key) is the communication bus between stages.
"""

import os

from google.adk.agents import LlmAgent, LoopAgent, ParallelAgent, SequentialAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, SseConnectionParams

from app import config
from app.context.rag.rag_tools import make_rag_retrieval_tool
from app.agent_repo.trip_planner_agent.prompt import (
    BUDGET_PRE_ASSESSOR_INSTRUCTION,
    DESTINATION_RESEARCHER_INSTRUCTION,
    FINAL_RESPONSE_INSTRUCTION,
    FLIGHT_HOTEL_SCOUT_INSTRUCTION,
    HUMAN_HANDOFF_INSTRUCTION,
    ITINERARY_BUILDER_INSTRUCTION,
    QUALITY_REVIEWER_INSTRUCTION,
    RESPONSE_ROUTER_INSTRUCTION,
    TRIAGE_ORCHESTRATOR_INSTRUCTION,
)

_MCP_SERVER_URL = os.getenv("FETCH_URL_MCP_SERVER", "http://localhost:3001/sse")

# RAG retrieval tool – None when corpus is unavailable (graceful degradation)
_rag_tool = make_rag_retrieval_tool()
_rag_tools = [_rag_tool] if _rag_tool else []

# ---------------------------------------------------------------------------
# Stage 1 — Triage: gather user input into session state
# ---------------------------------------------------------------------------

triage_orchestrator = LlmAgent(
    name="triage_orchestrator",
    model=config.DEFAULT_LLM_MODEL,
    description="Collects destination, dates, traveller count, and preferences from the user.",
    instruction=TRIAGE_ORCHESTRATOR_INSTRUCTION,
    output_key="trip_details",
)

# ---------------------------------------------------------------------------
# Stage 2 — Research fan-out: three specialists run in parallel
# ---------------------------------------------------------------------------

destination_researcher = LlmAgent(
    name="destination_researcher",
    model=config.DEFAULT_LLM_MODEL,
    description="Researches attractions, culture, weather, and tips for the destination.",
    instruction=DESTINATION_RESEARCHER_INSTRUCTION,
    tools=[
        McpToolset(
            connection_params=SseConnectionParams(url=_MCP_SERVER_URL),
            tool_filter=["fetch_url"],
        ),
        *_rag_tools,
    ],
    output_key="destination_research",
)

# google_search only — avoids the built-in / MCP mixing conflict.
flight_hotel_scout = LlmAgent(
    name="flight_hotel_scout",
    model=config.DEFAULT_LLM_MODEL,
    description="Finds flight options, hotel choices, and price ranges.",
    instruction=FLIGHT_HOTEL_SCOUT_INSTRUCTION,
    tools=[google_search],
    output_key="flight_hotel_data",
)

budget_pre_assessor = LlmAgent(
    name="budget_pre_assessor",
    model=config.DEFAULT_LLM_MODEL,
    description="Produces an initial rough budget estimate for the trip.",
    instruction=BUDGET_PRE_ASSESSOR_INSTRUCTION,
    output_key="budget_estimate",
)

research_fan_out = ParallelAgent(
    name="research_fan_out",
    description="Runs destination research, flight/hotel scouting, and budget estimation in parallel.",
    sub_agents=[destination_researcher, flight_hotel_scout, budget_pre_assessor],
)

# ---------------------------------------------------------------------------
# Stage 3 — Refinement loop: build → review → revise (max 2 cycles)
# ---------------------------------------------------------------------------

def _seed_loop_state(callback_context: CallbackContext) -> None:
    """Seed loop-scoped session keys on the first iteration so template vars exist."""
    for key in ("review_decision", "itinerary"):
        if key not in callback_context.state:
            callback_context.state[key] = ""


itinerary_builder = LlmAgent(
    name="itinerary_builder",
    model=config.DEFAULT_LLM_MODEL,
    description="Builds or revises a day-by-day itinerary from all research outputs.",
    instruction=ITINERARY_BUILDER_INSTRUCTION,
    tools=[*_rag_tools],
    output_key="itinerary",
    before_agent_callback=_seed_loop_state,
)

quality_reviewer = LlmAgent(
    name="quality_reviewer",
    model=config.DEFAULT_LLM_MODEL,
    description="Reviews the itinerary for quality and risk; routes to APPROVED, NEEDS_REVISION, or NEEDS_HUMAN.",
    instruction=QUALITY_REVIEWER_INSTRUCTION,
    output_key="review_decision",
)

refinement_loop = LoopAgent(
    name="refinement_loop",
    description="Iteratively builds and reviews the itinerary until approved or max iterations reached.",
    sub_agents=[itinerary_builder, quality_reviewer],
    max_iterations=2,
)

# ---------------------------------------------------------------------------
# Stage 4 — Conditional routing to terminal agents
# ---------------------------------------------------------------------------

final_response_agent = LlmAgent(
    name="final_response_agent",
    model=config.DEFAULT_LLM_MODEL,
    description="Formats and delivers the completed trip plan to the user.",
    instruction=FINAL_RESPONSE_INSTRUCTION,
)

human_handoff_agent = LlmAgent(
    name="human_handoff_agent",
    model=config.DEFAULT_LLM_MODEL,
    description="Escalates to a human travel agent and explains why.",
    instruction=HUMAN_HANDOFF_INSTRUCTION,
)

response_router = LlmAgent(
    name="response_router",
    model=config.DEFAULT_LLM_MODEL,
    description="Reads the quality review decision and routes to the appropriate terminal agent.",
    instruction=RESPONSE_ROUTER_INSTRUCTION,
    sub_agents=[final_response_agent, human_handoff_agent],
    tools=[
        AgentTool(agent=final_response_agent),
        AgentTool(agent=human_handoff_agent),
    ],
)

# ---------------------------------------------------------------------------
# Root — sequential pipeline driving all four stages
# ---------------------------------------------------------------------------

trip_planner_agent = SequentialAgent(
    name="trip_planner_agent",
    description="Plans complete trips end-to-end: research, flights, itinerary, and budget.",
    sub_agents=[
        triage_orchestrator,   # Stage 1: gather input
        research_fan_out,      # Stage 2: parallel research (fan-out)
        refinement_loop,       # Stage 3: build + review loop (fan-in → conditional)
        response_router,       # Stage 4: conditional routing to terminal agents
    ],
)
