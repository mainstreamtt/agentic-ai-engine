FROM python:3.12-slim

WORKDIR /app

# Install the ADK (includes A2A server utilities) and uvicorn
RUN pip install --no-cache-dir \
    "google-adk>=2.0.0b1" \
    "uvicorn>=0.34.0"

# Copy only this server's files
COPY __init__.py agent.py prompt.py server.py ./

EXPOSE 8001

# Suppress the a2a-experimental warning in production logs
ENV ADK_SUPPRESS_A2A_EXPERIMENTAL_FEATURE_WARNINGS=true

# GOOGLE_API_KEY must be supplied at runtime:
#   docker run -e GOOGLE_API_KEY=... -p 8001:8001 summarizer-critic
# For Vertex AI instead of API-key auth, set GOOGLE_GENAI_USE_VERTEXAI=TRUE
# and mount application default credentials.

CMD ["python", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
