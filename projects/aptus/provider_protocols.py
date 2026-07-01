"""Portfolio excerpt, adapted. Provider protocols for pluggable adapters.

Capabilities sit behind these contracts. Concrete adapters (Qdrant or pgvector,
Anthropic or OpenAI, self-hosted or managed database) are wired at startup, and
callers depend on the Protocol, never the implementation.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Protocol

# --------------------------------------------------------------------------- #
# Vector store
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class VectorHit:
    item_id: str
    score: float
    payload: dict[str, Any]


class VectorStoreProvider(Protocol):
    async def upsert(
        self, collection: str, item_id: str, vector: list[float], payload: dict[str, Any]
    ) -> None: ...
    async def search(
        self,
        collection: str,
        vector: list[float],
        top_k: int = 10,
        where: dict[str, Any] | None = None,
    ) -> list[VectorHit]: ...
    async def delete(self, collection: str, item_id: str) -> None: ...


# --------------------------------------------------------------------------- #
# LLM gateway
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class ChatMessage:
    role: str  # one of: system, user, assistant, tool
    content: str
    name: str | None = None


@dataclass(frozen=True, slots=True)
class ChatRequest:
    messages: tuple[ChatMessage, ...]
    profile_ref: str
    temperature: float | None = None
    max_tokens: int | None = None
    json_schema: dict[str, Any] | None = None
    tenant_id: str | None = None
    trace_id: str | None = None


@dataclass(frozen=True, slots=True)
class ChatResponse:
    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost_cents: int
    trace_id: str | None
    raw: dict[str, Any]


class LLMGateway(Protocol):
    async def chat(self, request: ChatRequest) -> ChatResponse: ...
    def stream_chat(self, request: ChatRequest) -> AsyncIterator[str]: ...
    async def healthcheck(self) -> bool: ...


# --------------------------------------------------------------------------- #
# Embeddings
# --------------------------------------------------------------------------- #


class EmbeddingProvider(Protocol):
    @property
    def dimensions(self) -> int: ...
    async def embed_one(self, text: str) -> list[float]: ...
    async def embed_batch(self, texts: list[str]) -> list[list[float]]: ...


# --------------------------------------------------------------------------- #
# Database
# --------------------------------------------------------------------------- #


class DatabaseProvider(Protocol):
    """Manage async engine and session lifecycle.

    Adapters resolve the URL secret and tune the connection pool.
    """

    async def connect(self) -> None: ...
    async def disconnect(self) -> None: ...
    async def healthcheck(self) -> bool: ...
    def dsn(self) -> str: ...


__all__ = [
    "VectorHit",
    "VectorStoreProvider",
    "ChatMessage",
    "ChatRequest",
    "ChatResponse",
    "LLMGateway",
    "EmbeddingProvider",
    "DatabaseProvider",
]
