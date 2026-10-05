import hashlib
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class SourceType(str, Enum):
    ICAI_STUDY_MATERIAL = "ICAI_STUDY_MATERIAL"
    RTP = "RTP"
    MTP = "MTP"
    PAST_EXAM = "PAST_EXAM"
    SATHI_GENERATED = "SATHI_GENERATED"


def calculate_content_hash(text: str) -> str:
    """Computes deterministic SHA-256 hash of normalized content."""
    normalized = " ".join(text.strip().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class KnowledgeChunkMetadata(BaseModel):
    document_id: str
    document_title: str
    source_type: SourceType = SourceType.ICAI_STUDY_MATERIAL
    issuing_body: str = "ICAI"
    stage: str = "Intermediate"
    group_name: Optional[str] = "Group 1"
    paper: str = "Taxation"
    module: Optional[str] = None
    chapter: str = "General"
    topic: Optional[str] = None
    statutory_reference: Optional[str] = None
    page_number: int = 1
    document_version: str = "2024-2025 Edition"
    effective_date: Optional[str] = "2024-05-01"
    content_hash: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class IngestedDocumentMetadata(BaseModel):
    document_id: str
    file_name: str
    file_path: Optional[str] = None
    file_format: str  # PDF, TXT, MD
    file_hash: str
    document_title: str
    source_type: SourceType = SourceType.ICAI_STUDY_MATERIAL
    issuing_body: str = "ICAI"
    stage: str = "Intermediate"
    group_name: Optional[str] = "Group 1"
    paper: str = "Taxation"
    module: Optional[str] = None
    chapter: Optional[str] = None
    total_pages: int = 1
    total_chunks: int = 0
    document_version: str = "2024-2025 Edition"
    effective_date: Optional[str] = "2024-05-01"

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()
