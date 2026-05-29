"""OpenTelemetry setup – routes ADK traces and metrics to GCP.

Uses ADK's built-in GCP exporters so no extra packages are required.

Telemetry destinations:
  - Cloud Trace    – agent runs, LLM calls, tool calls (spans)
  - Cloud Monitoring – latency / invocation metrics

Structured application logs are handled by structlog (see config.py),
so Cloud Logging via OTEL is intentionally disabled here to avoid duplicates.

Controlled by the OTEL_ENABLED env var (default: true on Cloud Run, false locally).
The OTEL_SERVICE_NAME env var labels all telemetry (default: "agentic-ai-engine").
"""

from __future__ import annotations

import structlog

from app import config

logger = structlog.get_logger(__name__)


def setup_telemetry() -> None:
    """Initialise the global OTEL providers and wire them to GCP exporters.

    Must be called once at application startup, before any ADK runners are
    created.  If setup fails the app continues without telemetry.
    """
    if not config.OTEL_ENABLED:
        logger.info("OpenTelemetry disabled", hint="set OTEL_ENABLED=true to enable")
        return

    try:
        from google.adk.telemetry.google_cloud import get_gcp_exporters, get_gcp_resource
        from google.adk.telemetry.setup import maybe_set_otel_providers

        gcp_hooks = get_gcp_exporters(
            enable_cloud_tracing=True,
            enable_cloud_metrics=True,
            # Structured logs are already handled by structlog → Cloud Logging;
            # enabling OTEL logging here would produce duplicates.
            enable_cloud_logging=False,
        )

        resource = get_gcp_resource(project_id=config.GOOGLE_CLOUD_PROJECT)

        maybe_set_otel_providers(
            otel_hooks_to_setup=[gcp_hooks],
            otel_resource=resource,
        )

        logger.info(
            "OpenTelemetry configured",
            project=config.GOOGLE_CLOUD_PROJECT,
            service=config.OTEL_SERVICE_NAME,
            destinations=["cloud_trace", "cloud_monitoring"],
        )

    except Exception:
        logger.warning(
            "OpenTelemetry setup failed – continuing without telemetry",
            exc_info=True,
        )
