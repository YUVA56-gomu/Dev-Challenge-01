import sqlite3
import re
from typing import List, Dict, Any, Optional
from app.db.database import get_connection, DB_PATH
from app.knowledge.document_store import KnowledgeDocumentStore, serialize_f32, HAS_SQLITE_VEC
from app.knowledge.embedding_provider import get_embedding_provider
from app.knowledge.document_parser import STATUTORY_PATTERN


class HybridKnowledgeRetriever:
    """
    Advanced Hybrid RAG Retriever for CA statutory knowledge:
    - FTS5 BM25 lexical search (with statutory query boosting)
    - sqlite-vec dense vector search (FastEmbed bge-small-en-v1.5)
    - Reciprocal Rank Fusion (RRF) with k=60
    - Exact Section/Standard dominance
    - Source provenance categorization (Official ICAI vs Sathi Generated)
    """

    def __init__(self, store: Optional[KnowledgeDocumentStore] = None):
        self.store = store or KnowledgeDocumentStore()
        self.embedding_provider = get_embedding_provider()

    def _get_connection(self) -> sqlite3.Connection:
        return self.store._get_connection()

    def search_keyword(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()

        # Sanitize query for FTS5
        clean_q = re.sub(r"[^\w\s]", " ", query).strip()
        tokens = [t for t in clean_q.split() if len(t) > 2]
        if not tokens:
            conn.close()
            return []

        fts_query = " OR ".join(tokens)

        # Check if an exact statutory section is present in query (e.g. Section 17, AS 10)
        stat_matches = STATUTORY_PATTERN.findall(query)
        if stat_matches:
            # Boost statutory section
            stat_token = stat_matches[0].replace("(", " ").replace(")", " ")
            fts_query = f'"{stat_matches[0]}" OR {fts_query}'

        try:
            cursor.execute("""
            SELECT
                f.chunk_id,
                bm25(knowledge_fts) as score,
                c.document_title,
                c.source_type,
                c.issuing_body,
                c.stage,
                c.paper,
                c.chapter,
                c.topic,
                c.statutory_reference,
                c.page_number,
                c.content
            FROM knowledge_fts f
            JOIN knowledge_chunks c ON f.chunk_id = c.chunk_id
            WHERE knowledge_fts MATCH ?
            ORDER BY bm25(knowledge_fts)
            LIMIT ?;
            """, (fts_query, limit))

            rows = [dict(r) for r in cursor.fetchall()]
            conn.close()
            return rows
        except Exception as e:
            conn.close()
            return []

    def search_semantic(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        if not HAS_SQLITE_VEC:
            return []

        query_vector = self.embedding_provider.embed_query(query)
        serialized_vec = serialize_f32(query_vector)

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
            SELECT
                c.chunk_id,
                v.distance as distance,
                c.document_title,
                c.source_type,
                c.issuing_body,
                c.stage,
                c.paper,
                c.chapter,
                c.topic,
                c.statutory_reference,
                c.page_number,
                c.content
            FROM knowledge_vec v
            JOIN knowledge_chunks c ON v.rowid = c.rowid
            WHERE v.embedding MATCH ? AND k = ?
            ORDER BY distance ASC;
            """, (serialized_vec, limit))

            rows = [dict(r) for r in cursor.fetchall()]
            conn.close()
            return rows
        except Exception as e:
            conn.close()
            return []

    def hybrid_search(self, query: str, limit: int = 4) -> List[Dict[str, Any]]:
        """
        Combines Lexical (BM25) and Semantic (Dense) rankings using Reciprocal Rank Fusion (RRF).
        RRF Score = SUM( 1 / (k + rank) )
        """
        k = 60
        scores: Dict[str, float] = {}
        items: Dict[str, Dict[str, Any]] = {}

        keyword_hits = self.search_keyword(query, limit=limit * 2)
        semantic_hits = self.search_semantic(query, limit=limit * 2)

        # Check if query has an explicit statutory section
        is_statutory = bool(STATUTORY_PATTERN.search(query))
        bm25_weight = 1.8 if is_statutory else 1.0

        for rank, hit in enumerate(keyword_hits, start=1):
            c_id = hit["chunk_id"]
            scores[c_id] = scores.get(c_id, 0.0) + (bm25_weight / (k + rank))
            if c_id not in items:
                items[c_id] = hit

        for rank, hit in enumerate(semantic_hits, start=1):
            c_id = hit["chunk_id"]
            scores[c_id] = scores.get(c_id, 0.0) + (1.0 / (k + rank))
            if c_id not in items:
                items[c_id] = hit

        # Fallback to existing rag_documents if knowledge_chunks is empty
        if not scores:
            from app.core.rag.vector_store import get_vector_store
            legacy_store = get_vector_store()
            legacy_hits = legacy_store.hybrid_search(query, limit=limit)
            return [
                {
                    "chunk_id": h.get("id", "legacy"),
                    "document_title": h.get("document_name", "ICAI Study Material"),
                    "source_type": "ICAI_STUDY_MATERIAL",
                    "issuing_body": "ICAI",
                    "stage": h.get("stage", "Intermediate"),
                    "paper": h.get("paper", "CA Paper"),
                    "chapter": h.get("chapter", "General"),
                    "topic": h.get("topic", ""),
                    "statutory_reference": h.get("statutory_reference", ""),
                    "page_number": h.get("page_number", 1),
                    "content": h.get("content", ""),
                    "score": h.get("rrf_score", 0.5),
                    "is_official": True,
                    "provenance_label": "🏛️ Official ICAI Source"
                }
                for h in legacy_hits
            ]

        # Sort by RRF score descending
        sorted_ids = sorted(scores.keys(), key=lambda cid: scores[cid], reverse=True)[:limit]

        results = []
        for cid in sorted_ids:
            item = items[cid]
            src_type = item.get("source_type", "ICAI_STUDY_MATERIAL")
            is_off = (src_type != "SATHI_GENERATED")
            prov_label = "🏛️ Official ICAI Source" if is_off else "🤖 Sathi AI Generated Practice"

            results.append({
                "chunk_id": cid,
                "document_title": item.get("document_title"),
                "source_type": src_type,
                "issuing_body": item.get("issuing_body", "ICAI"),
                "stage": item.get("stage"),
                "paper": item.get("paper"),
                "chapter": item.get("chapter"),
                "topic": item.get("topic"),
                "statutory_reference": item.get("statutory_reference"),
                "page_number": item.get("page_number"),
                "content": item.get("content"),
                "score": round(scores[cid], 4),
                "is_official": is_off,
                "provenance_label": prov_label
            })

        return results


_default_retriever = None

def get_knowledge_retriever() -> HybridKnowledgeRetriever:
    global _default_retriever
    if _default_retriever is None:
        _default_retriever = HybridKnowledgeRetriever()
    return _default_retriever
