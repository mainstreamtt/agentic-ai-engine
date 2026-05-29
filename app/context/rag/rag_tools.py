"""RAG retrieval tool – lazy factory wrapping VertexAiRagRetrieval.

Usage in an agent:
    from app.context.rag.rag_tools import make_rag_retrieval_tool

    _rag_tool = make_rag_retrieval_tool()

    my_agent = LlmAgent(
        ...
        tools=[*([_rag_tool] if _rag_tool else [])],
    )

For Gemini 2+ models the tool is injected as built-in RAG grounding, so
retrieved knowledge-base context is automatically included in every call
without the agent needing to invoke a function explicitly.
"""

from __future__ import annotations

import structlog

from google.adk.tools.retrieval import VertexAiRagRetrieval

from app.context.rag.rag_engine_handler import rag_engine_handler

logger = structlog.get_logger(__name__)


def make_rag_retrieval_tool() -> VertexAiRagRetrieval | None:
    """Return a configured VertexAiRagRetrieval tool, or None if unavailable.

    Triggers lazy corpus initialisation on first call.
    """
    corpus = rag_engine_handler.corpus_name
    if not corpus:
        logger.warning("RAG corpus unavailable – skipping RAG tool")
        return None

    logger.info("RAG retrieval tool created", corpus=corpus)
    return VertexAiRagRetrieval(
        name="search_knowledge_base",
        description=(
            "Search the internal travel knowledge base for curated destination "
            "guides, practical tips, budget advice, and packing information. "
            "Use this alongside live web searches to ground responses in "
            "reliable, pre-vetted travel content."
        ),
        rag_corpora=[corpus],
        similarity_top_k=5,
        vector_distance_threshold=0.5,
    )
