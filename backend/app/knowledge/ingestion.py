import os
import hashlib
from typing import Dict, Any, Optional, List
from app.knowledge.document_parser import get_parser_for_file, ParsedDocument
from app.knowledge.chunker import SemanticChunker, SemanticChunk
from app.knowledge.metadata import (
    KnowledgeChunkMetadata,
    IngestedDocumentMetadata,
    SourceType,
    calculate_content_hash
)
from app.knowledge.document_store import KnowledgeDocumentStore


def calculate_file_hash(file_path: str) -> str:
    """Calculates SHA-256 hash of entire file bytes for document-level deduplication."""
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest()


class KnowledgeIngestionEngine:
    """
    Production-quality ingestion engine:
    Document -> Parser -> Text Extraction -> Page & Section Detection ->
    Semantic Chunking -> Metadata Extraction -> Content Hash -> SQLite FTS5 -> sqlite-vec
    """

    def __init__(self, store: Optional[KnowledgeDocumentStore] = None):
        self.store = store or KnowledgeDocumentStore()
        self.chunker = SemanticChunker(target_chunk_size=800, max_chunk_size=1500)

    def ingest_file(
        self,
        file_path: str,
        metadata_overrides: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Parses and indexes a file (PDF, TXT, MD) into the knowledge base.
        Enforces duplicate protection based on SHA-256 file hash and chunk hashes.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        merged_overrides = dict(metadata_overrides or {})
        merged_overrides.update(kwargs)
        metadata_overrides = merged_overrides

        file_name = os.path.basename(file_path)
        ext = os.path.splitext(file_name)[1].lower().replace(".", "").upper()
        file_hash = calculate_file_hash(file_path)

        # 1. Check duplicate at document level
        existing = self.store.get_document_by_hash(file_hash)
        if existing:
            return {
                "status": "already_indexed",
                "message": f"Document '{existing['document_title']}' is already indexed. Existing chunks: {existing['total_chunks']}, Skipped duplicates: {existing['total_chunks']}",
                "document_id": existing["document_id"],
                "existing_chunks": existing["total_chunks"],
                "skipped_duplicates": existing["total_chunks"]
            }

        # 2. Parse Document
        parser = get_parser_for_file(file_path)
        custom_title = (metadata_overrides or {}).get("document_title")
        parsed_doc: ParsedDocument = parser.parse(file_path, title=custom_title)

        doc_id = f"doc_{file_hash[:12]}"
        doc_title = custom_title or parsed_doc.title or file_name

        # Merge metadata overrides
        overrides = metadata_overrides or {}
        source_type_val = overrides.get("source_type", SourceType.ICAI_STUDY_MATERIAL)
        if isinstance(source_type_val, str):
            try:
                source_type_val = SourceType(source_type_val)
            except ValueError:
                source_type_val = SourceType.ICAI_STUDY_MATERIAL

        stage = overrides.get("stage", "Intermediate")
        group_name = overrides.get("group_name", "Group 1")
        paper = overrides.get("paper", "Taxation")
        module = overrides.get("module", None)
        chapter = overrides.get("chapter", parsed_doc.detected_chapters[0] if parsed_doc.detected_chapters else "General")
        issuing_body = overrides.get("issuing_body", "ICAI")
        doc_ver = overrides.get("document_version", "2024-2025 Edition")
        eff_date = overrides.get("effective_date", "2024-05-01")

        base_chunk_meta = KnowledgeChunkMetadata(
            document_id=doc_id,
            document_title=doc_title,
            source_type=source_type_val,
            issuing_body=issuing_body,
            stage=stage,
            group_name=group_name,
            paper=paper,
            module=module,
            chapter=chapter,
            document_version=doc_ver,
            effective_date=eff_date
        )

        # 3. Chunk Document
        chunks: List[SemanticChunk] = self.chunker.chunk_document(parsed_doc, base_chunk_meta)

        # 4. Create Document Registry Metadata
        doc_meta = IngestedDocumentMetadata(
            document_id=doc_id,
            file_name=file_name,
            file_path=os.path.abspath(file_path),
            file_format=ext,
            file_hash=file_hash,
            document_title=doc_title,
            source_type=source_type_val,
            issuing_body=issuing_body,
            stage=stage,
            group_name=group_name,
            paper=paper,
            module=module,
            chapter=chapter,
            total_pages=parsed_doc.total_pages,
            total_chunks=len(chunks),
            document_version=doc_ver,
            effective_date=eff_date
        )

        # 5. Store & Index in SQLite / FTS5 / sqlite-vec
        res = self.store.store_document(doc_meta, chunks)
        return res

    def ingest_directory(
        self,
        directory_path: str,
        default_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        results = []
        if not os.path.exists(directory_path):
            return results

        for root, _, files in os.walk(directory_path):
            for file in files:
                if file.lower().endswith((".pdf", ".md", ".txt")):
                    full_p = os.path.join(root, file)
                    try:
                        res = self.ingest_file(full_p, metadata_overrides=default_metadata)
                        results.append(res)
                    except Exception as e:
                        results.append({
                            "status": "error",
                            "file": file,
                            "error": str(e)
                        })
        return results


_default_engine = None

def get_ingestion_engine() -> KnowledgeIngestionEngine:
    global _default_engine
    if _default_engine is None:
        _default_engine = KnowledgeIngestionEngine()
    return _default_engine
