"""MCP server exposing a fetch_url tool via SSE transport.

Architecture (matches the hands-on diagram):
  Agent/Client  --HTTP SSE (port 3001)-->  Starlette ASGI app
                                              └─ FastMCP SSE handler (/ route)
                                                   └─ fetch_url tool
                                                        └─ httpx  -->  external web page
"""

import uvicorn
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    name="fetch-url-server",
    host="0.0.0.0",
    port=3001,
)


@mcp.tool()
async def fetch_url(url: str) -> str:
    """Fetch the content of a web page and return it as plain text.

    Args:
        url: The full URL of the page to retrieve (e.g. https://example.com).

    Returns:
        The HTTP response body as a UTF-8 string, or an error message.
    """
    async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text


if __name__ == "__main__":
    # mcp.sse_app() returns a Starlette ASGI app with the SSE handler at /sse
    app = mcp.sse_app()
    uvicorn.run(app, host="0.0.0.0", port=3001)
