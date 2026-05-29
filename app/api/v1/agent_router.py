"""Agent listing API – v1."""

import asyncio
import base64

from fastapi import APIRouter, Query
from fastapi.responses import Response
from pydantic import BaseModel

from app.agent_repo import list_agents
from app import config
from app.context.artifacts.artifact_service_handler import artifact_service_handler
from app.context.memory.memory_bank_handler import memory_bank_handler
from app.context.rag.rag_engine_handler import rag_engine_handler
from app.handlers.session_handler import session_handler

agent_router = APIRouter(prefix="/api/v1", tags=["agents"])


@agent_router.get("/agents")
async def get_agents() -> dict:
    """Return all registered agents and the current default."""
    return {"agents": list_agents(), "default": config.DEFAULT_AGENT_ID}


@agent_router.get("/artifacts")
async def get_artifacts(agent_id: str = Query(..., description="Agent ID")) -> dict:
    """Return all artifact filenames for the given agent across all sessions."""
    app_name = f"{agent_id}_app"
    svc = artifact_service_handler.service
    if not hasattr(svc, "storage_client"):
        return {"artifacts": []}

    user_prefix = f"{app_name}/{config.USER_ID}/"

    def _list_all() -> list[str]:
        filenames: set[str] = set()
        for blob in svc.storage_client.list_blobs(svc.bucket, prefix=user_prefix):
            relative = blob.name[len(user_prefix):]
            parts = relative.split("/")
            if len(parts) >= 3:
                filename = "/".join(parts[1:-1])
                # Strip internal user: prefix before returning to the UI
                if filename.startswith("user:"):
                    filename = filename[5:]
                if filename:
                    filenames.add(filename)
        return sorted(filenames)

    return {"artifacts": await asyncio.to_thread(_list_all)}


@agent_router.get("/artifacts/download")
async def download_artifact(
    agent_id: str = Query(..., description="Agent ID"),
    filename: str = Query(..., description="Artifact filename"),
) -> Response:
    """Download the latest version of an artifact, searching across all sessions."""
    app_name = f"{agent_id}_app"
    svc = artifact_service_handler.service
    if not hasattr(svc, "storage_client"):
        return Response(content="Artifact service unavailable", status_code=503)

    user_prefix = f"{app_name}/{config.USER_ID}/"

    def _find_scope_and_gcs_name() -> tuple[str, str] | None:
        """Return (scope, gcs_filename) for the latest version of filename."""
        best_scope: str | None = None
        best_gcs_name: str | None = None
        best_version = -1
        # Match both user-scoped ("user:filename") and legacy session-scoped ("filename")
        targets = {f"user:{filename}", filename}
        for blob in svc.storage_client.list_blobs(svc.bucket, prefix=user_prefix):
            relative = blob.name[len(user_prefix):]
            parts = relative.split("/")
            if len(parts) < 3:
                continue
            scope = parts[0]
            candidate = "/".join(parts[1:-1])
            if candidate not in targets:
                continue
            try:
                version = int(parts[-1])
                if version > best_version:
                    best_version = version
                    best_scope = scope
                    best_gcs_name = candidate
            except ValueError:
                pass
        if best_scope is None or best_gcs_name is None:
            return None
        return best_scope, best_gcs_name

    result = await asyncio.to_thread(_find_scope_and_gcs_name)
    if result is None:
        return Response(content="Artifact not found", status_code=404)

    scope, gcs_filename = result
    # "user" scope means user-namespaced artifact (session_id=None)
    session_id = None if scope == "user" else scope
    part = await svc.load_artifact(
        app_name=app_name,
        user_id=config.USER_ID,
        session_id=session_id,
        filename=gcs_filename,
    )
    if part is None:
        return Response(content="Artifact not found", status_code=404)

    if part.text:
        data = part.text.encode("utf-8")
        mime = "text/plain"
    elif part.inline_data:
        data = part.inline_data.data
        mime = part.inline_data.mime_type or "application/octet-stream"
    else:
        return Response(content="Artifact has no content", status_code=404)

    return Response(
        content=data,
        media_type=mime,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@agent_router.get("/memories")
async def get_memories(
    agent_id: str = Query(..., description="Agent ID"),
    query: str = Query("*", description="Search query for memory facts"),
) -> dict:
    """Return memory facts for the given agent's user scope."""
    app_name = f"{agent_id}_app"
    if memory_bank_handler.service is None:
        return {"memories": [], "error": "Memory bank not available"}
    try:
        result = await memory_bank_handler.service.search_memory(
            app_name=app_name,
            user_id=config.USER_ID,
            query=query,
        )
        facts = [
            {
                "text": entry.content.parts[0].text if entry.content and entry.content.parts else "",
                "timestamp": entry.timestamp or "",
            }
            for entry in (result.memories or [])
        ]
        return {"memories": facts}
    except Exception as e:
        return {"memories": [], "error": str(e)}


# ── RAG corpus management ───────────────────────────────────────────────


@agent_router.get("/rag/files")
async def get_rag_files() -> dict:
    """List all files in the RAG corpus."""
    if not rag_engine_handler.available:
        return {"files": [], "error": "RAG engine not available"}
    return {"files": await rag_engine_handler.list_files()}


class RagImportRequest(BaseModel):
    gcs_uris: list[str]


@agent_router.post("/rag/import")
async def import_rag_files(body: RagImportRequest) -> dict:
    """Import files from GCS URIs into the RAG corpus."""
    if not rag_engine_handler.available:
        return {"status": "error", "message": "RAG engine not available"}
    return await rag_engine_handler.import_files(body.gcs_uris)


@agent_router.delete("/rag/files")
async def delete_rag_file(
    file_name: str = Query(..., description="RAG file resource name"),
) -> dict:
    """Delete a file from the RAG corpus."""
    if not rag_engine_handler.available:
        return {"status": "error", "message": "RAG engine not available"}
    return await rag_engine_handler.delete_file(file_name)
