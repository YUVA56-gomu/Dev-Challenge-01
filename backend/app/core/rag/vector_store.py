import sqlite3
import os
import numpy as np
from typing import List, Dict, Optional, Tuple
from abc import ABC, abstractmethod
from app.db.database import get_connection, DB_PATH
from app.core.rag.document_store import DocumentChunk, get_official_icai_seed_documents, save_processed_documents

try:
    import sqlite_vec
    HAS_SQLITE_VEC = True
except ImportError:
    HAS_SQLITE_VEC = False

try:
    from fastembed import TextEmbedding
    HAS_FASTEMBED = True
except ImportError:
    HAS_FASTEMBED = False

class VectorStore(ABC):
    """Abstract VectorStore interface for pluggable storage."""
    
    @abstractmethod
    def add_documents(self, documents: List[DocumentChunk]):
        pass

    @abstractmethod
    def search_keyword(self, query: str, limit: int = 4) -> List[Dict]:
        pass

    @abstractmethod
    def search_semantic(self, query: str, limit: int = 4) -> List[Dict]:
        pass

    @abstractmethod
    def hybrid_search(self, query: str, limit: int = 4) -> List[Dict]:
        pass

class SQLiteVectorStore(VectorStore):
    """
    Local-first hybrid vector store using:
    - SQLite FTS5 for BM25 lexical/statutory keyword search (Section 17(5), AS 10, SA 200, etc.)
    - sqlite-vec for 384-dimensional vector embeddings
    - FastEmbed (BAAI/bge-small-en-v1.5) running locally on CPU/ONNX
    - Reciprocal Rank Fusion (RRF) for balanced hybrid ranking
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._embedding_model = None
        self._init_tables()
        self._ensure_seed_documents()

    def _get_embedding_model(self):
        if self._embedding_model is None and HAS_FASTEMBED:
            try:
                self._embedding_model = TextEmbedding("BAAI/bge-small-en-v1.5")
            except Exception as e:
                print(f"[VectorStore] Warning: Could not initialize fastembed: {e}")
        return self._embedding_model

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        if HAS_SQLITE_VEC:
            try:
                conn.enable_load_extension(True)
                sqlite_vec.load(conn)
            except Exception as e:
                pass
        return conn

    def _init_tables(self):
        conn = self._get_connection()
        cursor = conn.cursor()

        # 1. Base Document Store Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS rag_documents (
            id TEXT PRIMARY KEY,
            document_name TEXT NOT NULL,
            source TEXT NOT NULL,
            version_date TEXT NOT NULL,
            stage TEXT NOT NULL,
            group_name TEXT NOT NULL,
            paper TEXT NOT NULL,
            module TEXT NOT NULL,
            chapter TEXT NOT NULL,
            topic TEXT NOT NULL,
            page_number INTEGER NOT NULL,
            statutory_reference TEXT NOT NULL,
            content TEXT NOT NULL
        );
        """)

        # 2. FTS5 Virtual Table for Lexical/Keyword Retrieval
        cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS rag_fts USING fts5(
            doc_id UNINDEXED,
            statutory_reference,
            topic,
            chapter,
            paper,
            content,
            tokenize = 'porter unicode61'
        );
        """)

        # 3. sqlite-vec Virtual Table for Dense Vector Embeddings (float[384])
        if HAS_SQLITE_VEC:
            try:
                cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS rag_vec USING vec0(
                    rowid INTEGER PRIMARY KEY,
                    embedding float[384]
                );
                """)
            except Exception as e:
                print(f"[VectorStore] Warning creating rag_vec: {e}")

        conn.commit()
        conn.close()

    def _ensure_seed_documents(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM rag_documents;")
        count = cursor.fetchone()[0]
        conn.close()

        if count == 0:
            seed_docs = get_official_icai_seed_documents()
            save_processed_documents(seed_docs)
            self.add_documents(seed_docs)

    def add_documents(self, documents: List[DocumentChunk]):
        conn = self._get_connection()
        cursor = conn.cursor()

        embed_model = self._get_embedding_model()
        texts_to_embed = [f"{d.statutory_reference} {d.topic} {d.chapter}: {d.content}" for d in documents]
        embeddings = []
        if embed_model:
            try:
                embeddings = list(embed_model.embed(texts_to_embed))
            except Exception as e:
                print(f"[VectorStore] Failed to generate embeddings: {e}")

        for idx, doc in enumerate(documents):
            # Insert document
            cursor.execute("""
            INSERT OR REPLACE INTO rag_documents (
                id, document_name, source, version_date, stage, group_name,
                paper, module, chapter, topic, page_number, statutory_reference, content
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                doc.chunk_id, doc.document_name, doc.source, doc.version_date,
                doc.stage, doc.group_name, doc.paper, doc.module, doc.chapter,
                doc.topic, doc.page_number, doc.statutory_reference, doc.content
            ))

            # Insert into FTS5
            cursor.execute("DELETE FROM rag_fts WHERE doc_id = ?;", (doc.chunk_id,))
            cursor.execute("""
            INSERT INTO rag_fts (doc_id, statutory_reference, topic, chapter, paper, content)
            VALUES (?, ?, ?, ?, ?, ?);
            """, (doc.chunk_id, doc.statutory_reference, doc.topic, doc.chapter, doc.paper, doc.content))

            # Insert into sqlite-vec
            if HAS_SQLITE_VEC and idx < len(embeddings):
                try:
                    cursor.execute("SELECT rowid FROM rag_documents WHERE id = ?;", (doc.chunk_id,))
                    doc_rowid = cursor.fetchone()[0]
                    emb = np.array(embeddings[idx], dtype=np.float32)
                    cursor.execute("DELETE FROM rag_vec WHERE rowid = ?;", (doc_rowid,))
                    cursor.execute("INSERT INTO rag_vec(rowid, embedding) VALUES (?, ?);", (doc_rowid, emb))
                except Exception as e:
                    print(f"[VectorStore] Could not insert vector into rag_vec: {e}")

        conn.commit()
        conn.close()

    def search_keyword(self, query: str, limit: int = 4) -> List[Dict]:
        """Performs BM25 keyword search using FTS5."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Sanitize query for FTS5 (strip punctuation that breaks FTS syntax)
        sanitized = "".join([c if c.isalnum() or c.isspace() else " " for c in query]).strip()
        tokens = [t for t in sanitized.split() if len(t) > 1]
        if not tokens:
            conn.close()
            return []

        fts_query = " OR ".join(tokens)

        try:
            cursor.execute("""
                SELECT doc_id, bm25(rag_fts) as rank_score
                FROM rag_fts
                WHERE rag_fts MATCH ?
                ORDER BY rank_score ASC
                LIMIT ?;
            """, (fts_query, limit))
            rows = cursor.fetchall()
            
            results = []
            for r in rows:
                cursor.execute("SELECT * FROM rag_documents WHERE id = ?;", (r["doc_id"],))
                doc_row = cursor.fetchone()
                if doc_row:
                    d = dict(doc_row)
                    d["keyword_score"] = float(r["rank_score"])
                    results.append(d)
            conn.close()
            return results
        except Exception as e:
            print(f"[VectorStore] FTS5 search error: {e}")
            conn.close()
            return []

    def search_semantic(self, query: str, limit: int = 4) -> List[Dict]:
        """Performs dense vector similarity search using sqlite-vec."""
        if not HAS_SQLITE_VEC:
            return []

        embed_model = self._get_embedding_model()
        if not embed_model:
            return []

        try:
            query_emb = list(embed_model.embed([query]))[0]
            query_vec = np.array(query_emb, dtype=np.float32)

            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT rowid, distance
                FROM rag_vec
                WHERE embedding MATCH ? AND k = ?;
            """, (query_vec, limit))
            rows = cursor.fetchall()

            results = []
            for r in rows:
                target_rowid = r["rowid"]
                cursor.execute("SELECT * FROM rag_documents WHERE rowid = ?;", (target_rowid,))
                doc_row = cursor.fetchone()
                if doc_row:
                    doc = dict(doc_row)
                    doc["semantic_distance"] = float(r["distance"])
                    doc["semantic_similarity"] = max(0.0, 1.0 - float(r["distance"]))
                    results.append(doc)

            conn.close()
            return results
        except Exception as e:
            print(f"[VectorStore] Semantic search error: {e}")
            return []


    def hybrid_search(self, query: str, limit: int = 3) -> List[Dict]:
        """
        Combines keyword (FTS5 BM25) and dense semantic retrieval (sqlite-vec)
        using Reciprocal Rank Fusion (RRF):
        RRF Score = (0.5 / (60 + rank_keyword)) + (0.5 / (60 + rank_semantic))
        """
        keyword_hits = self.search_keyword(query, limit=limit * 2)
        semantic_hits = self.search_semantic(query, limit=limit * 2)

        if not semantic_hits:
            return keyword_hits[:limit]
        if not keyword_hits:
            return semantic_hits[:limit]

        # Reciprocal Rank Fusion
        doc_scores = {}
        doc_map = {}

        # 1. Score keyword hits
        for rank, doc in enumerate(keyword_hits):
            doc_id = doc["id"]
            doc_map[doc_id] = doc
            doc_scores[doc_id] = doc_scores.get(doc_id, 0.0) + (1.0 / (60.0 + rank + 1.0))

        # 2. Score semantic hits
        for rank, doc in enumerate(semantic_hits):
            doc_id = doc["id"]
            if doc_id not in doc_map:
                doc_map[doc_id] = doc
            doc_scores[doc_id] = doc_scores.get(doc_id, 0.0) + (1.2 / (60.0 + rank + 1.0))

        # 3. Sort by combined RRF score
        sorted_doc_ids = sorted(doc_scores.keys(), key=lambda k: doc_scores[k], reverse=True)
        final_results = []
        for did in sorted_doc_ids[:limit]:
            doc = doc_map[did]
            doc["rrf_score"] = doc_scores[did]
            final_results.append(doc)

        return final_results

_vector_store_instance = None

def get_vector_store() -> VectorStore:
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = SQLiteVectorStore()
    return _vector_store_instance
