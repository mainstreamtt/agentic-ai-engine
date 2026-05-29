"""Agent registry – maps agent_id to LlmAgent instances and display metadata.

To add a new agent:
  1. Create a new sub-package under agent_repo/
  2. Import the agent here
  3. Add an entry to AGENT_REGISTRY
"""

from google.adk.agents import LlmAgent

from app.agent_repo.greeting_agent import greeting_agent
from app.agent_repo.summarizer_agent import summarizer_agent
from app.agent_repo.trip_planner_agent import trip_planner_agent

AGENT_REGISTRY: dict[str, dict] = {
    "greeting_agent": {
        "agent": greeting_agent,
        "label": "Welcome",
        "description": "Welcomes students and helps them get started.",
        "icon": "👋",
        "has_artifacts": False,
        "has_memory": True,
        "has_rag": False,
    },
    "summarizer_agent": {
        "agent": summarizer_agent,
        "label": "Summarizer",
        "description": "Summarizes conversations and provides helpful overviews.",
        "icon": "📝",
        "has_artifacts": True,
        "has_memory": True,
        "has_rag": False,
    },
    "trip_planner_agent": {
        "agent": trip_planner_agent,
        "label": "Trip Planner",
        "description": "Plans complete trips: destination research, flights, itinerary, and budget.",
        "icon": "✈️",
        "has_artifacts": False,
        "has_memory": False,
        "has_rag": False,
    },
}


def get_agent(agent_id: str) -> LlmAgent:
    """Look up an agent by ID. Raises KeyError if not found."""
    entry = AGENT_REGISTRY[agent_id]
    return entry["agent"]


def list_agents() -> list[dict]:
    """Return metadata for all registered agents (for the UI)."""
    from app.context.memory.memory_bank_handler import memory_bank_handler
    memory_available = memory_bank_handler.service is not None

    return [
        {
            "id": agent_id,
            "label": meta["label"],
            "description": meta["description"],
            "icon": meta["icon"],
            "has_artifacts": meta.get("has_artifacts", False),
            "has_memory": meta.get("has_memory", False) and memory_available,
            "has_rag": meta.get("has_rag", False),
        }
        for agent_id, meta in AGENT_REGISTRY.items()
    ]
