"""Entry point: expose the summarizer_critic LlmAgent as an A2A server.

Run locally:
    python server.py

Run in Docker (see Dockerfile):
    docker run -e GOOGLE_API_KEY=... -p 8001:8001 summarizer-critic

The agent card is served at:  http://localhost:8001/.well-known/agent.json
A2A endpoint:                 http://localhost:8001/
"""

import os
import sys

# Suppress ADK experimental warnings before any ADK import
os.environ.setdefault("ADK_SUPPRESS_A2A_EXPERIMENTAL_FEATURE_WARNINGS", "true")
os.environ.setdefault("ADK_SUPPRESS_EXPERIMENTAL_FEATURE_WARNINGS", "true")

# Load .env for local development (no-op when env vars are already set, e.g. Cloud Run)
from dotenv import load_dotenv
load_dotenv()

import uvicorn
from google.adk.a2a.utils.agent_to_a2a import to_a2a

# Support both `python server.py` (standalone) and `python -m app.a2a_agents.summarizer_critic.server`
if __package__:
    from .agent import critic_agent
else:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))
    from app.a2a_agents.summarizer_critic.agent import critic_agent

HOST = os.getenv("CRITIC_A2A_HOST", "0.0.0.0")
PORT = int(os.getenv("CRITIC_A2A_PORT", "8001"))

# to_a2a returns a Starlette ASGI application.
# The agent card is auto-built from the agent's name / description.
app = to_a2a(
    critic_agent,
    host=HOST,
    port=PORT,
    protocol="http",
)

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)
