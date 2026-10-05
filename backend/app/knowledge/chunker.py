import re
from typing import List, Dict, Any, Optional
from app.knowledge.document_parser import ParsedDocument, STATUTORY_PATTERN
from app.knowledge.metadata import KnowledgeChunkMetadata, calculate_content_hash, SourceType


class SemanticChunk:
    def __init__(
        self,
        chunk_id: str,
        content: str,
        metadata: KnowledgeChunkMetadata
    ):
        self.chunk_id = chunk_id
        self.content = content.strip()
        self.metadata = metadata

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "metadata": self.metadata.to_dict()
        }


class SemanticChunker:
    """
    Chunks parsed documents respecting structural statutory and heading boundaries.
    Preserves full legal clauses (sub-sections, provisos, explanations) without truncating.
    """

    def __init__(self, target_chunk_size: int = 800, max_chunk_size: int = 1500):
        self.target_chunk_size = target_chunk_size
        self.max_chunk_size = max_chunk_size

    def chunk_document(
        self,
        parsed_doc: ParsedDocument,
        base_metadata: KnowledgeChunkMetadata
    ) -> List[SemanticChunk]:
        chunks: List[SemanticChunk] = []
        chunk_counter = 1

        for page in parsed_doc.pages:
            page_text = page.text.strip()
            if not page_text:
                continue

            # Split by double newlines or statutory clause breaks
            paragraphs = self._split_paragraphs(page_text)
            current_buffer = []
            current_len = 0
            current_stats = set(page.statutory_references)

            for para in paragraphs:
                para_len = len(para)
                # Check for statutory sections inside this paragraph
                para_stats = STATUTORY_PATTERN.findall(para)
                for ps in para_stats:
                    current_stats.add(ps)

                if current_len + para_len > self.target_chunk_size and current_buffer:
                    # Flush current buffer as a completed chunk
                    chunk_text = "\n\n".join(current_buffer).strip()
                    c_hash = calculate_content_hash(chunk_text)
                    stat_ref = ", ".join(list(current_stats)[:3]) if current_stats else base_metadata.statutory_reference

                    chunk_meta = base_metadata.model_copy(update={
                        "page_number": page.page_number,
                        "statutory_reference": stat_ref,
                        "content_hash": c_hash
                    })

                    c_id = f"{base_metadata.document_id}_p{page.page_number}_c{chunk_counter}"
                    chunks.append(SemanticChunk(chunk_id=c_id, content=chunk_text, metadata=chunk_meta))
                    chunk_counter += 1

                    current_buffer = [para]
                    current_len = para_len
                    current_stats = set(para_stats)
                else:
                    current_buffer.append(para)
                    current_len += para_len

            if current_buffer:
                chunk_text = "\n\n".join(current_buffer).strip()
                c_hash = calculate_content_hash(chunk_text)
                stat_ref = ", ".join(list(current_stats)[:3]) if current_stats else base_metadata.statutory_reference

                chunk_meta = base_metadata.model_copy(update={
                    "page_number": page.page_number,
                    "statutory_reference": stat_ref,
                    "content_hash": c_hash
                })

                c_id = f"{base_metadata.document_id}_p{page.page_number}_c{chunk_counter}"
                chunks.append(SemanticChunk(chunk_id=c_id, content=chunk_text, metadata=chunk_meta))
                chunk_counter += 1

        return chunks

    def _split_paragraphs(self, text: str) -> List[str]:
        # Split on paragraph breaks or numbered clauses: (a), (b), (i), (ii), Proviso, Explanation
        raw_paras = re.split(r"\n\s*\n|(?<=\.)\s*\n(?=\([a-z0-9]+\)|\bProvided\b|\bExplanation\b)", text)
        clean = []
        for p in raw_paras:
            s = p.strip()
            if s:
                clean.append(s)
        return clean if clean else [text.strip()]
