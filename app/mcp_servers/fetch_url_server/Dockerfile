FROM python:3.12-slim

WORKDIR /app

# Install only the dependencies needed by the MCP server
RUN pip install --no-cache-dir \
    "mcp[cli]>=1.27.0" \
    "httpx>=0.28.0" \
    "uvicorn>=0.34.0" \
    "starlette>=0.41.0"

COPY server.py .

EXPOSE 3001

CMD ["python", "server.py"]
