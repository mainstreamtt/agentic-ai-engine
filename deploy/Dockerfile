# ── Stage 1: dependency installer ────────────────────────────────────────────
# Installs production dependencies into a virtual environment.
# Source code is NOT copied here so that a code-only change does not bust the
# layer that runs `uv sync` (the most expensive layer).
FROM python:3.14-slim AS builder

WORKDIR /app

# Bring in uv from its official image (avoids installing via pip/curl).
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Compile bytecode and copy files instead of symlinking (required for
# the venv to be portable across stages).
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Install deps first — this layer is cached as long as the lock file is unchanged.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# ── Stage 2: runtime image ────────────────────────────────────────────────────
FROM python:3.14-slim

WORKDIR /app

# Copy the pre-built virtual environment from the builder stage.
COPY --from=builder /app/.venv /app/.venv

# Copy application source code.
COPY agentic_ai_main.py ./
COPY app/ ./app/

# Activate the venv by adding it to PATH.
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Cloud Run injects PORT=8080; this is the fallback for local `docker run`.
    PORT=8080

# Run as a non-root user (Cloud Run best practice).
RUN useradd --create-home --uid 1000 appuser && chown -R appuser /app
USER appuser

# Single-worker uvicorn: Cloud Run scales by spawning new container instances,
# not by adding processes inside one instance.  Multi-worker would also break
# in-process WebSocket state sharing.
CMD ["sh", "-c", "exec uvicorn agentic_ai_main:app --host 0.0.0.0 --port ${PORT} --workers 1"]
