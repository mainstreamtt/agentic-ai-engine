"""Application entrypoint – launches the FastAPI server with WebSocket chat."""

import os

import uvicorn

from app.config import configure_logging
from app.api.fastapi_app import create_app
from app.context.observability.telemetry import setup_telemetry

# Configure structured logging before anything else
configure_logging()

# Initialise OTEL before ADK runners are created so every span is captured.
setup_telemetry()

# Module-level app instance (used by uvicorn in both local and Cloud Run)
app = create_app()


def main() -> None:
    """Start the uvicorn server for local development."""

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "agentic_ai_main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        reload_dirs=["app"],
    )


if __name__ == "__main__":
    main()
