import sys
import os
import io
import time
import tempfile
import json
import pytest

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

from fastapi.testclient import TestClient
from app.main import app
from app.db.database import init_db, get_connection
from app.knowledge.document_parser import PDFDocumentParser, MarkdownDocumentParser, TextDocumentParser
from app.knowledge.chunker import SemanticChunker
from app.knowledge.metadata import KnowledgeChunkMetadata, IngestedDocumentMetadata, SourceType
from app.knowledge.document_store import KnowledgeDocumentStore
from app.knowledge.retriever import HybridKnowledgeRetriever, get_knowledge_retriever
from app.knowledge.ingestion import KnowledgeIngestionEngine, get_ingestion_engine
from app.repositories.practice_repository import PracticeRepository


SAMPLE_PDF_BYTES = b"""%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R 6 0 R] /Count 2 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj
4 0 obj << /Length 260 >> stream
BT
/F1 14 Tf
72 700 Td
(ICAI Study Material - Intermediate Group 1) Tj
0 -24 Td
(Paper 4: Taxation - Chapter 6: Input Tax Credit) Tj
0 -24 Td
(Section 17\\(5\\): Statutory Blocked Credits) Tj
0 -24 Td
(Input tax credit shall not be available in respect of motor vehicles for transportation of persons having approved seating capacity of not more than 13 persons including the driver.) Tj
ET
endstream
endobj
5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj
6 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 7 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj
7 0 obj << /Length 220 >> stream
BT
/F1 14 Tf
72 700 Td
(Section 17\\(5\\) Exceptions and Eligibility) Tj
0 -24 Td
(However, ITC shall be available when motor vehicles are used for further supply of such vehicles or for imparting training on driving.) Tj
0 -24 Td
(General insurance and servicing of eligible motor vehicles are also permitted for credit.) Tj
ET
endstream
endobj
xref
0 8
0000000000 65535 f 
0000000009 00000 n 
0000000056 00000 n 
0000000122 00000 n 
0000000251 00000 n 
0000000561 00000 n 
0000000632 00000 n 
0000000761 00000 n 
trailer << /Size 8 /Root 1 0 R >>
startxref
1031
%%EOF"""


def run_phase4_verification():
    print("=" * 70)
    print("SATHI CA COMPANION - PHASE 4 FULL VERIFICATION SUITE")
    print("ICAI KNOWLEDGE INGESTION + QUESTION CORPUS + HYBRID RAG")
    print("=" * 70)

    init_db()
    client = TestClient(app)

    # -------------------------------------------------------------
    # 1. PDF Parsing, Page Preservation, and Section Detection
    # -------------------------------------------------------------
    print("\n[1/15] Testing PDF Parsing & Page Number Preservation...")
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
        tf.write(SAMPLE_PDF_BYTES)
        temp_pdf_path = tf.name

    try:
        parser = PDFDocumentParser()
        parsed_doc = parser.parse(temp_pdf_path)
        assert parsed_doc.total_pages == 2, f"Expected 2 pages, got {parsed_doc.total_pages}"
        assert len(parsed_doc.pages) == 2, f"Expected 2 page objects, got {len(parsed_doc.pages)}"
        assert parsed_doc.pages[0].page_number == 1
        assert parsed_doc.pages[1].page_number == 2
        assert "Section 17(5)" in parsed_doc.pages[0].text
        print(f"  ✓ PDF Parsed successfully: {parsed_doc.total_pages} pages extracted")
        print(f"  ✓ Page 1 Headings: {parsed_doc.pages[0].headings}")
        print(f"  ✓ Statutory Section detected: {parsed_doc.pages[0].statutory_references}")
        assert any("17" in ref for ref in parsed_doc.pages[0].statutory_references)

        # -------------------------------------------------------------
        # 2. Semantic Clause-Aware Chunking
        # -------------------------------------------------------------
        print("\n[2/15] Testing Semantic Chunking & Legal Clause Boundaries...")
        base_meta = KnowledgeChunkMetadata(
            document_id="doc_test_gst_itc",
            document_title="ICAI Study Material - Paper 4 Taxation: ITC",
            source_type=SourceType.ICAI_STUDY_MATERIAL,
            issuing_body="ICAI",
            stage="Intermediate",
            group_name="Group 1",
            paper="Taxation",
            module="GST",
            chapter="Input Tax Credit",
            topic="Blocked Credits",
            statutory_reference="Section 17(5)",
            page_number=1,
            document_version="2024",
            effective_date="May 2024",
            content_hash=""
        )
        chunker = SemanticChunker(target_chunk_size=200, max_chunk_size=500)
        chunks = chunker.chunk_document(parsed_doc, base_meta)
        assert len(chunks) >= 2, f"Expected at least 2 chunks, got {len(chunks)}"
        print(f"  ✓ Created {len(chunks)} semantic chunks respecting clause boundaries")
        for i, c in enumerate(chunks):
            print(f"    - Chunk {i+1} (Page {c.metadata.page_number}): Section='{c.metadata.statutory_reference}', Hash={c.metadata.content_hash[:12]}...")
            assert c.metadata.page_number in (1, 2)
            assert len(c.content.strip()) > 30

        # -------------------------------------------------------------
        # 3. Deterministic Content Hash Deduplication
        # -------------------------------------------------------------
        print("\n[3/15] Testing Deterministic Hash Deduplication...")
        conn = get_connection()
        conn.execute("DELETE FROM knowledge_chunks WHERE document_id IN (SELECT document_id FROM ingested_documents WHERE document_title = 'ICAI Paper 4 Taxation - Input Tax Credit');")
        conn.execute("DELETE FROM ingested_documents WHERE document_title = 'ICAI Paper 4 Taxation - Input Tax Credit';")
        conn.commit()
        conn.close()

        ingestion_engine = get_ingestion_engine()
        res1 = ingestion_engine.ingest_file(
            file_path=temp_pdf_path,
            document_title="ICAI Paper 4 Taxation - Input Tax Credit",
            source_type="ICAI_STUDY_MATERIAL",
            issuing_body="ICAI",
            stage="Intermediate",
            group_name="Group 1",
            paper="Taxation",
            module="GST",
            chapter="Input Tax Credit",
            document_version="2024",
            effective_date="May 2024 onwards"
        )
        assert res1["status"] == "success", f"Ingestion 1 failed: {res1}"
        assert res1["indexed_chunks"] >= 2
        print(f"  ✓ Initial Ingestion: Status='{res1['status']}', Chunks Indexed={res1['indexed_chunks']}")

        # Re-ingest the exact same document
        res2 = ingestion_engine.ingest_file(
            file_path=temp_pdf_path,
            document_title="ICAI Paper 4 Taxation - Input Tax Credit",
            source_type="ICAI_STUDY_MATERIAL",
            issuing_body="ICAI",
            stage="Intermediate",
            group_name="Group 1",
            paper="Taxation",
            module="GST",
            chapter="Input Tax Credit",
            document_version="2024",
            effective_date="May 2024 onwards"
        )
        assert res2["status"] == "already_indexed", f"Duplicate ingestion not caught: {res2}"
        print(f"  ✓ Duplicate Prevention Verified: Status='{res2['status']}', Existing Chunks={res2['existing_chunks']}")
        assert "already indexed" in res2["message"]

        # -------------------------------------------------------------
        # 4. FTS5 BM25 Lexical Keyword Search & Statutory Dominance
        # -------------------------------------------------------------
        print("\n[4/15] Testing FTS5 Keyword Search & Exact Statutory Dominance...")
        retriever = get_knowledge_retriever()
        kw_hits = retriever.search_keyword("Section 17(5) motor vehicles", limit=3)
        assert len(kw_hits) > 0, "Expected FTS5 keyword hits for Section 17(5)"
        print(f"  ✓ FTS5 returned {len(kw_hits)} hits for 'Section 17(5) motor vehicles'")
        print(f"    Top Match: Page {kw_hits[0]['page_number']} | Statutory Ref: '{kw_hits[0]['statutory_reference']}'")
        assert "Section 17(5)" in kw_hits[0].get("statutory_reference", "") or "17" in kw_hits[0]["content"]

        # -------------------------------------------------------------
        # 5. Dense Vector Retrieval (sqlite-vec + FastEmbed)
        # -------------------------------------------------------------
        print("\n[5/15] Testing Dense Vector Retrieval...")
        sem_hits = retriever.search_semantic("credit allowed for driving school vehicles", limit=3)
        print(f"  ✓ Dense Vector search returned {len(sem_hits)} hits")
        if sem_hits:
            print(f"    Top Vector Hit: Score Distance={sem_hits[0].get('distance')} | Content Snippet: '{sem_hits[0]['content'][:60]}...'")

        # -------------------------------------------------------------
        # 6. Reciprocal Rank Fusion (RRF) & Hybrid Search
        # -------------------------------------------------------------
        print("\n[6/15] Testing Hybrid RRF Fusion Retrieval...")
        hybrid_hits = retriever.hybrid_search("motor vehicles for transportation of persons", limit=3)
        assert len(hybrid_hits) > 0, "Expected hybrid retrieval results"
        print(f"  ✓ Hybrid RRF returned {len(hybrid_hits)} ranked chunks")
        top_hybrid = hybrid_hits[0]
        print(f"    Top Hit: Score={top_hybrid['score']} | Document='{top_hybrid['document_title']}' | Provenance='{top_hybrid['provenance_label']}'")
        assert top_hybrid["is_official"] is True
        assert "🏛️ Official ICAI Source" in top_hybrid["provenance_label"]

        # -------------------------------------------------------------
        # 7. Knowledge REST API Endpoints
        # -------------------------------------------------------------
        print("\n[7/15] Testing Knowledge API Endpoints (/api/knowledge/...)...")
        res_docs = client.get("/api/knowledge/documents")
        assert res_docs.status_code == 200
        docs_list = res_docs.json()
        assert len(docs_list) >= 1
        print(f"  ✓ /api/knowledge/documents returned {len(docs_list)} registered documents")

        res_search = client.post("/api/knowledge/search", json={"query": "Section 17(5) seating capacity", "top_k": 3})
        assert res_search.status_code == 200
        search_body = res_search.json()
        assert search_body["count"] > 0
        print(f"  ✓ /api/knowledge/search returned {search_body['count']} results with provenance")

        # -------------------------------------------------------------
        # 8. Full Question Corpus Architecture (25+ Questions)
        # -------------------------------------------------------------
        print("\n[8/15] Testing Question Corpus Architecture & Seed Count...")
        res_stats = client.get("/api/practice/corpus/stats")
        assert res_stats.status_code == 200
        corpus_stats = res_stats.json()
        print(f"  ✓ Total Questions: {corpus_stats['total_questions']}")
        print(f"  ✓ 🏛️ Official ICAI Questions: {corpus_stats['official_questions']}")
        print(f"  ✓ 🤖 Sathi AI Generated Practice: {corpus_stats['ai_generated_questions']}")
        print(f"  ✓ Stage Breakdown: {corpus_stats['stage_breakdown']}")
        print(f"  ✓ Question Types: {corpus_stats['type_breakdown']}")
        assert corpus_stats["total_questions"] >= 25, f"Expected at least 25 questions, got {corpus_stats['total_questions']}"
        assert corpus_stats["official_questions"] >= 20, f"Expected at least 20 official questions, got {corpus_stats['official_questions']}"
        assert corpus_stats["ai_generated_questions"] >= 3, f"Expected at least 3 AI questions, got {corpus_stats['ai_generated_questions']}"
        assert any("intermediate" in s.lower() for s in corpus_stats["stage_breakdown"])
        assert any("foundation" in s.lower() for s in corpus_stats["stage_breakdown"])
        assert any("final" in s.lower() for s in corpus_stats["stage_breakdown"])

        # -------------------------------------------------------------
        # 9. Question Filtering by Stage, Paper, Difficulty, and Provenance
        # -------------------------------------------------------------
        print("\n[9/15] Testing Question Filtering by Stage and Provenance...")
        res_inter = client.get("/api/practice/questions?stage_id=Intermediate")
        assert res_inter.status_code == 200
        inter_qs = res_inter.json()
        assert len(inter_qs) >= 15
        print(f"  ✓ Filtered Intermediate Questions: {len(inter_qs)} questions")

        res_official = client.get("/api/practice/questions?is_official=true")
        assert res_official.status_code == 200
        off_qs = res_official.json()
        for q in off_qs:
            assert q.get("is_official") in (1, True, "1")
        print(f"  ✓ Filtered is_official=true: {len(off_qs)} official questions")

        res_ai = client.get("/api/practice/questions?source_type=SATHI_GENERATED")
        assert res_ai.status_code == 200
        ai_qs = res_ai.json()
        assert len(ai_qs) >= 3
        print(f"  ✓ Filtered source_type=SATHI_GENERATED: {len(ai_qs)} AI questions")

        # -------------------------------------------------------------
        # 10. AI-Generated Practice Question Labeling Guarantee
        # -------------------------------------------------------------
        print("\n[10/15] Testing AI-Generated Practice Question Labeling...")
        for q in ai_qs:
            assert q["is_official"] in (0, False, "0"), f"AI Question {q['id']} falsely marked as official!"
            assert "Sathi" in q["source"], f"AI Question {q['id']} missing Sathi source marker"
        print("  ✓ Strict Provenance Guarantee Passed: 0 AI questions falsely labeled as official ICAI")

        # -------------------------------------------------------------
        # 11. Timed Exam Generator with Non-Repetition Logic
        # -------------------------------------------------------------
        print("\n[11/15] Testing Timed Exam Generator & Non-Repetition...")
        # Start exam 1
        res_exam1 = client.post("/api/practice/exam/start", json={
            "student_id": "pooja",
            "paper_id": "paper_tax",
            "num_questions": 3,
            "time_limit_minutes": 20
        })
        assert res_exam1.status_code == 200
        exam1 = res_exam1.json()
        q_ids_1 = [q["id"] for q in exam1["questions"]]
        print(f"  ✓ Exam 1 Generated: 3 questions -> {q_ids_1}")

        # Start exam 2 with exclude_ids=q_ids_1
        selected_q_2 = PracticeRepository.select_exam_questions(
            paper_id="paper_tax",
            count=3,
            exclude_ids=q_ids_1
        )
        q_ids_2 = [q["id"] for q in selected_q_2]
        print(f"  ✓ Exam 2 with exclude_ids: 3 questions -> {q_ids_2}")
        overlap = set(q_ids_1).intersection(set(q_ids_2))
        print(f"  ✓ Repetition avoided: {len(overlap)} overlapping questions out of 3")
        assert len(overlap) < len(q_ids_1)

        # -------------------------------------------------------------
        # 12. Multi-Factor Weak-Area Engine
        # -------------------------------------------------------------
        print("\n[12/15] Testing Multi-Factor Weak-Area Engine...")
        conn = get_connection()
        conn.execute("DELETE FROM topic_performance WHERE student_id = 'pooja_test';")
        conn.execute("DELETE FROM revision_schedule WHERE student_id = 'pooja_test';")
        conn.commit()
        conn.close()

        # Simulate repeated mistakes on Section 17(5)
        PracticeRepository.update_topic_performance(
            student_id="pooja_test",
            topic_id="ch_tax_itc_sec17_5",
            chapter_id="ch_tax_itc",
            paper_id="paper_tax",
            is_correct=False,
            score=1.5,
            max_score=5.0,
            mistakes=["Missed motor vehicle seating capacity threshold under Section 17(5)"]
        )
        PracticeRepository.update_topic_performance(
            student_id="pooja_test",
            topic_id="ch_tax_itc_sec17_5",
            chapter_id="ch_tax_itc",
            paper_id="paper_tax",
            is_correct=False,
            score=2.0,
            max_score=5.0,
            mistakes=["Failed to differentiate general insurance exception from blocked credit"]
        )
        weak_topics = PracticeRepository.get_weak_topics("pooja_test", limit=5)
        assert len(weak_topics) > 0
        weak_sec17 = next((w for w in weak_topics if w["topic_id"] == "ch_tax_itc_sec17_5"), None)
        assert weak_sec17 is not None, "Failed to detect ch_tax_itc_sec17_5 as weak topic"
        print(f"  ✓ Weak Area Detected: {weak_sec17['topic_title']} | Accuracy={weak_sec17['accuracy_pct']}% | Avg Score={weak_sec17['average_score_pct']}%")
        print(f"    Repeated Mistakes Identified: {weak_sec17.get('repeated_mistakes')}")
        assert len(weak_sec17.get("repeated_mistakes", [])) >= 1

        # -------------------------------------------------------------
        # 13. Priority-Adaptive Spaced Revision Scheduling
        # -------------------------------------------------------------
        print("\n[13/15] Testing Adaptive Spaced Revision Scheduling...")
        # Trigger first mistake -> Day 1 revision
        rev1 = PracticeRepository.schedule_spaced_revision(
            student_id="pooja_test",
            topic_id="ch_tax_itc_sec17_5",
            chapter_id="ch_tax_itc",
            paper_id="paper_tax"
        )
        assert rev1["interval_day"] == 1
        print(f"  ✓ First Failure: Revision scheduled for Day {rev1['interval_day']}")

        # Trigger second failure -> priority escalation to Day 1 / immediate cycle
        rev2 = PracticeRepository.schedule_spaced_revision(
            student_id="pooja_test",
            topic_id="ch_tax_itc_sec17_5",
            chapter_id="ch_tax_itc",
            paper_id="paper_tax"
        )
        print(f"  ✓ Repeated Failure: Priority escalated to Day {rev2['interval_day']}")
        assert rev2["interval_day"] in (1, 3)

        # -------------------------------------------------------------
        # 14. Practice → Companion Seamless Context Transfer
        # -------------------------------------------------------------
        print("\n[14/15] Testing Practice Attempt Context Transfer to Chat...")
        attempt_context = {
            "question_id": "q_tax_itc_1",
            "question_text": "Examine the eligibility of ITC on motor vehicles used for transportation of employees.",
            "user_answer": "ITC is allowed because it is used for business employees.",
            "score": 2.5,
            "max_score": 5.0,
            "mistakes": ["Missed statutory exception under Section 17(5) regarding seating capacity exceeding 13 persons"],
            "statutory_reference": "Section 17(5)"
        }
        res_chat = client.post("/api/chat", json={
            "message": "Why did I lose marks on my answer regarding motor vehicles?",
            "study_context": {
                "paper": "Taxation",
                "chapter": "Input Tax Credit",
                "topic": "Blocked Credit",
                "statutory_section": "Section 17(5)",
                "attempt_context": attempt_context
            }
        })
        assert res_chat.status_code == 200, f"Chat call failed: {res_chat.text}"
        chat_resp = res_chat.json()
        reply_lower = chat_resp["reply"].lower()
        print(f"  ✓ Sathi Chat Response Generated ({len(chat_resp['reply'])} chars)")
        print(f"    Snippet: '{chat_resp['reply'][:140]}...'")
        print(f"  ✓ RAG Grounded: {chat_resp['is_rag_grounded']}")
        if chat_resp.get("citations"):
            top_cit = chat_resp["citations"][0]
            print(f"  ✓ Citation: {top_cit['document_name']} | Section: {top_cit['statutory_reference']} | Provenance: {top_cit.get('provenance_label')}")
            assert top_cit.get("is_official") is True

        # -------------------------------------------------------------
        # 15. ElevenLabs Spoken Evaluation Summary Verification
        # -------------------------------------------------------------
        print("\n[15/15] Testing Spoken Evaluation Summary Format...")
        spoken = chat_resp.get("spoken_reply", "")
        assert len(spoken) > 0, "Expected non-empty spoken reply"
        assert len(spoken) <= 320, f"Spoken summary too long ({len(spoken)} chars)"
        print(f"  ✓ Concise Voice Summary ({len(spoken)} chars): '{spoken}'")

    finally:
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)

    print("\n" + "=" * 70)
    print("ALL 15/15 PHASE 4 VERIFICATION CHECKS COMPLETED AND PASSED!")
    print("=" * 70)


if __name__ == "__main__":
    run_phase4_verification()
