import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import httpx
from app.core.rag.vector_store import get_vector_store
from app.core.rag.query_router import route_query


BASE_URL = "http://127.0.0.1:8000"

def test_rag_pipeline():
    print("=" * 60)
    print("SATHI CA COMPANION - PHASE 2 RAG VERIFICATION SUITE")
    print("=" * 60)

    vs = get_vector_store()

    # 1. Test Query Router (Fast vs Deep)
    print("\n[1/6] Testing Query Router (Fast Path vs Deep Path)...")
    fast_path, info_fast = route_query("Hey Sathi, good morning!")
    assert fast_path == "fast", f"Expected fast path, got {fast_path}"
    print(f"  ✓ 'Hey Sathi' routed to: {fast_path} ({info_fast.get('reason')})")

    deep_path_sec, info_deep = route_query("What are the blocked credits under Section 17(5)?")
    assert deep_path_sec == "deep", f"Expected deep path, got {deep_path_sec}"
    print(f"  ✓ 'Section 17(5)' routed to: {deep_path_sec} ({info_deep.get('reason')})")

    deep_path_ctx, info_ctx = route_query("Can we take credit on this?", active_context={"chapter": "Input Tax Credit"})
    assert deep_path_ctx == "deep", f"Expected deep path from context, got {deep_path_ctx}"
    print(f"  ✓ Query with active chapter context routed to: {deep_path_ctx}")

    # 2. Test Keyword Retrieval (Exact Section / Standard)
    print("\n[2/6] Testing Keyword Retrieval (FTS5 BM25)...")
    res_17_5 = vs.search_keyword("Section 17(5)")
    assert len(res_17_5) > 0, "Failed to retrieve Section 17(5)"
    print(f"  ✓ Retrieved: {res_17_5[0]['statutory_reference']} (Score: {res_17_5[0].get('keyword_score'):.3f})")
    assert "Section 17(5)" in res_17_5[0]['statutory_reference']

    res_139 = vs.search_keyword("Section 139")
    assert len(res_139) > 0, "Failed to retrieve Section 139"
    print(f"  ✓ Retrieved: {res_139[0]['statutory_reference']} (Topic: {res_139[0]['topic']})")
    assert "139" in res_139[0]['statutory_reference']

    # 3. Test Semantic Retrieval (Conceptual phrasing without section numbers)
    print("\n[3/6] Testing Semantic Retrieval (sqlite-vec + FastEmbed)...")
    res_sem_itc = vs.search_semantic("Can a company claim credit on motor cars purchased for its executives?")
    assert len(res_sem_itc) > 0, "Semantic retrieval returned empty"
    print(f"  ✓ Query: 'credit on motor cars' -> Topic: {res_sem_itc[0]['topic']} (Dist: {res_sem_itc[0].get('semantic_distance'):.3f})")
    assert "Section 17(5)" in res_sem_itc[0]['statutory_reference']

    res_sem_audit = vs.search_semantic("Why can't an auditor guarantee complete absence of fraud?")
    assert len(res_sem_audit) > 0, "Semantic audit retrieval returned empty"
    print(f"  ✓ Query: 'auditor guarantee fraud' -> Standard: {res_sem_audit[0]['statutory_reference']}")
    assert "200" in res_sem_audit[0]['statutory_reference'] and "SA" in res_sem_audit[0]['statutory_reference']


    # 4. Test Hybrid Search with Reciprocal Rank Fusion
    print("\n[4/6] Testing Hybrid Search & Reciprocal Rank Fusion (RRF)...")
    res_hybrid = vs.hybrid_search("Who appoints the first auditor of a company and within what timeframe?")
    assert len(res_hybrid) > 0, "Hybrid search failed"
    top_hit = res_hybrid[0]
    print(f"  ✓ Top Hit: {top_hit['topic']} | RRF Score: {top_hit.get('rrf_score', 0):.4f}")
    assert "139" in top_hit['statutory_reference'] or "Auditor" in top_hit['topic']

    # 5. Test Source Provenance & Metadata Integrity
    print("\n[5/6] Verifying Source Provenance and Metadata Integrity...")
    for doc in [top_hit]:
        assert doc['source'] == "ICAI Official Study Material"
        assert doc['stage'] == "Intermediate"
        assert doc['page_number'] > 0
        assert len(doc['version_date']) > 0
        print(f"  ✓ Document Provenance verified: {doc['document_name']} | Page {doc['page_number']} | {doc['version_date']}")

    # 6. End-to-End Chat API RAG Verification
    print("\n[6/6] Testing End-to-End Grounded Gemma Response & Citations...")
    with httpx.Client(base_url=BASE_URL, timeout=60.0) as client:
        chat_res = client.post("/api/chat", json={
            "message": "What is the rule under Section 17(5) for motor vehicles credit?"
        })
        assert chat_res.status_code == 200, f"Chat failed: {chat_res.text}"
        data = chat_res.json()
        print(f"  ✓ Grounded Flag: {data.get('is_rag_grounded')}")
        assert data.get('is_rag_grounded') is True
        citations = data.get('citations') or []
        assert len(citations) > 0, "Citations should not be empty for Deep Path"
        print(f"  ✓ Citations Count: {len(citations)}")
        print(f"  ✓ Citation 1: {citations[0]['statutory_reference']} (Page {citations[0]['page_number']})")
        print(f"  ✓ Response Preview: {data['reply'][:140]}...")

    print("\n" + "=" * 60)
    print("ALL RAG VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    test_rag_pipeline()
