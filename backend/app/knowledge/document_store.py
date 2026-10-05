import sqlite3
import struct
from typing import List, Dict, Any, Optional, Tuple
from app.db.database import get_connection, DB_PATH
from app.knowledge.metadata import KnowledgeChunkMetadata, IngestedDocumentMetadata, SourceType
from app.knowledge.chunker import SemanticChunk
from app.knowledge.embedding_provider import get_embedding_provider

try:
    import sqlite_vec
    HAS_SQLITE_VEC = True
except ImportError:
    HAS_SQLITE_VEC = False


def serialize_f32(vector: List[float]) -> bytes:
    """Serializes a float list to 32-bit little-endian IEEE-754 bytes for sqlite-vec."""
    return struct.pack(f"{len(vector)}f", *vector)


class KnowledgeDocumentStore:
    """
    Production-grade knowledge store with deterministic hash deduplication,
    FTS5 full-text indexing, and sqlite-vec 384d dense embeddings.
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._embedding_provider = get_embedding_provider()
        self._init_tables()

    def _get_connection(self) -> sqlite3.Connection:
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

        # 1. Ingested Documents Registry
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ingested_documents (
            document_id TEXT PRIMARY KEY,
            file_name TEXT NOT NULL,
            file_path TEXT,
            file_format TEXT NOT NULL,
            file_hash TEXT UNIQUE NOT NULL,
            document_title TEXT NOT NULL,
            source_type TEXT NOT NULL,
            issuing_body TEXT NOT NULL,
            stage TEXT NOT NULL,
            group_name TEXT,
            paper TEXT NOT NULL,
            module TEXT,
            chapter TEXT,
            total_pages INTEGER NOT NULL DEFAULT 1,
            total_chunks INTEGER NOT NULL DEFAULT 0,
            document_version TEXT,
            effective_date TEXT,
            ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 2. Knowledge Chunks with Provenance & Hashes
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_chunks (
            chunk_id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL REFERENCES ingested_documents(document_id) ON DELETE CASCADE,
            document_title TEXT NOT NULL,
            source_type TEXT NOT NULL,
            issuing_body TEXT NOT NULL,
            stage TEXT NOT NULL,
            group_name TEXT,
            paper TEXT NOT NULL,
            module TEXT,
            chapter TEXT NOT NULL,
            topic TEXT,
            statutory_reference TEXT,
            page_number INTEGER NOT NULL,
            document_version TEXT,
            effective_date TEXT,
            content TEXT NOT NULL,
            content_hash TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_kchunks_doc ON knowledge_chunks(document_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_kchunks_paper ON knowledge_chunks(paper);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_kchunks_statutory ON knowledge_chunks(statutory_reference);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_kchunks_hash ON knowledge_chunks(content_hash);")

        # 3. FTS5 Virtual Table for BM25 Lexical Keyword Search
        cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
            chunk_id UNINDEXED,
            document_title,
            statutory_reference,
            topic,
            chapter,
            paper,
            content,
            tokenize = 'porter unicode61'
        );
        """)

        # 4. sqlite-vec Dense Vector Table (384 dimensions)
        if HAS_SQLITE_VEC:
            try:
                cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_vec USING vec0(
                    rowid INTEGER PRIMARY KEY,
                    embedding float[384]
                );
                """)
            except Exception as e:
                pass

        conn.commit()
        conn.close()

    def get_document_by_hash(self, file_hash: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ingested_documents WHERE file_hash = ?;", (file_hash,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def store_document(
        self,
        doc_metadata: IngestedDocumentMetadata,
        chunks: List[SemanticChunk]
    ) -> Dict[str, Any]:
        """
        Stores document and chunks with deterministic duplicate protection.
        If document hash exists, returns duplicate message and skips.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Check existing document
        existing_doc = self.get_document_by_hash(doc_metadata.file_hash)
        if existing_doc:
            cursor.execute(
                "SELECT COUNT(*) FROM knowledge_chunks WHERE document_id = ?;",
                (existing_doc["document_id"],)
            )
            existing_chunks = cursor.fetchone()[0]
            conn.close()
            return {
                "status": "already_indexed",
                "message": f"Document '{doc_metadata.document_title}' already indexed.",
                "document_id": existing_doc["document_id"],
                "existing_chunks": existing_chunks,
                "skipped_duplicates": len(chunks)
            }

        # Insert document registry
        cursor.execute("""
        INSERT INTO ingested_documents (
            document_id, file_name, file_path, file_format, file_hash,
            document_title, source_type, issuing_body, stage, group_name,
            paper, module, chapter, total_pages, total_chunks,
            document_version, effective_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            doc_metadata.document_id, doc_metadata.file_name, doc_metadata.file_path,
            doc_metadata.file_format, doc_metadata.file_hash, doc_metadata.document_title,
            doc_metadata.source_type.value if hasattr(doc_metadata.source_type, 'value') else doc_metadata.source_type,
            doc_metadata.issuing_body, doc_metadata.stage, doc_metadata.group_name,
            doc_metadata.paper, doc_metadata.module, doc_metadata.chapter,
            doc_metadata.total_pages, len(chunks), doc_metadata.document_version,
            doc_metadata.effective_date
        ))

        # Filter out chunks that might have duplicate content hashes across the system
        inserted_chunks = 0
        skipped_chunk_duplicates = 0
        texts_to_embed = []
        chunks_to_embed = []

        for chunk in chunks:
            c_meta = chunk.metadata
            c_hash = c_meta.content_hash
            cursor.execute("SELECT chunk_id FROM knowledge_chunks WHERE content_hash = ?;", (c_hash,))
            if cursor.fetchone():
                skipped_chunk_duplicates += 1
                continue

            src_val = c_meta.source_type.value if hasattr(c_meta.source_type, 'value') else c_meta.source_type
            cursor.execute("""
            INSERT INTO knowledge_chunks (
                chunk_id, document_id, document_title, source_type, issuing_body,
                stage, group_name, paper, module, chapter, topic,
                statutory_reference, page_number, document_version,
                effective_date, content, content_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                chunk.chunk_id, doc_metadata.document_id, c_meta.document_title,
                src_val, c_meta.issuing_body, c_meta.stage, c_meta.group_name,
                c_meta.paper, c_meta.module, c_meta.chapter, c_meta.topic,
                c_meta.statutory_reference, c_meta.page_number, c_meta.document_version,
                c_meta.effective_date, chunk.content, c_hash
            ))

            # FTS5 Indexing
            cursor.execute("""
            INSERT INTO knowledge_fts (
                chunk_id, document_title, statutory_reference, topic, chapter, paper, content
            ) VALUES (?, ?, ?, ?, ?, ?, ?);
            """, (
                chunk.chunk_id, c_meta.document_title, c_meta.statutory_reference or "",
                c_meta.topic or "", c_meta.chapter, c_meta.paper, chunk.content
            ))

            texts_to_embed.append(chunk.content)
            chunks_to_embed.append(chunk)
            inserted_chunks += 1

        conn.commit()

        # Generate and store dense vector embeddings
        if HAS_SQLITE_VEC and texts_to_embed:
            try:
                embeddings = self._embedding_provider.embed_texts(texts_to_embed)
                for chunk, emb in zip(chunks_to_embed, embeddings):
                    cursor.execute("SELECT rowid FROM knowledge_chunks WHERE chunk_id = ?;", (chunk.chunk_id,))
                    row = cursor.fetchone()
                    if row:
                        row_id = row[0]
                        cursor.execute("""
                        INSERT OR REPLACE INTO knowledge_vec (rowid, embedding)
                        VALUES (?, ?);
                        """, (row_id, serialize_f32(emb)))
                conn.commit()
            except Exception as e:
                print(f"[KnowledgeStore] Notice: Vector embedding generation note: {e}")

        conn.close()

        return {
            "status": "success",
            "message": f"Successfully indexed '{doc_metadata.document_title}'.",
            "document_id": doc_metadata.document_id,
            "existing_chunks": 0,
            "indexed_chunks": inserted_chunks,
            "skipped_duplicates": skipped_chunk_duplicates
        }

    def list_documents(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ingested_documents ORDER BY ingested_at DESC;")
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def get_corpus_stats(self) -> Dict[str, Any]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ingested_documents;")
        docs_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM knowledge_chunks;")
        chunks_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT paper) FROM knowledge_chunks;")
        papers_count = cursor.fetchone()[0]
        conn.close()
        return {
            "total_documents": docs_count,
            "total_chunks": chunks_count,
            "covered_papers": papers_count
        }
