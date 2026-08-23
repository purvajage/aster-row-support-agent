from typing import Any

from pydantic import BaseModel, Field


class Source(BaseModel):
    filename: str
    heading: str


class RetrievedPassage(BaseModel):
    text: str
    source: Source
    metadata: dict[str, Any] = Field(default_factory=dict)
    score: float


class OrderLookupResult(BaseModel):
    found: bool
    order_id: str
    data: dict[str, Any] | None = None
    error: str | None = None


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source] = Field(default_factory=list)
    handoff: bool = False