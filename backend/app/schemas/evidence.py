"""Evidence API schemas."""

from pydantic import BaseModel, Field


class EvidenceItemSchema(BaseModel):
    id: str
    chunk_id: str
    document_id: str | None = None
    document_filename: str | None = None
    snippet: str
    relevance_score: float
    page_number: int | None = None


class EvidenceListSchema(BaseModel):
    recommendation_id: str
    items: list[EvidenceItemSchema] = Field(default_factory=list)
