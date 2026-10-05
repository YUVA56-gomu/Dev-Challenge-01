import httpx

BASE_URL = "http://127.0.0.1:8000"

def test_study_context():
    print("=" * 60)
    print("SATHI CA COMPANION - PHASE 2 STUDY & CONTEXT SUITE")
    print("=" * 60)

    with httpx.Client(base_url=BASE_URL, timeout=60.0) as client:
        # 1. Stages
        print("\n[1/5] Testing CA Stages Endpoint (/api/study/stages)...")
        res = client.get("/api/study/stages")
        assert res.status_code == 200, f"Stages failed: {res.text}"
        stages = res.json()
        stage_names = [s["name"] for s in stages]
        print(f"  ✓ Available Stages: {stage_names}")
        assert "CA Intermediate" in stage_names
        assert "CA Foundation" in stage_names
        assert "CA Final" in stage_names

        # 2. Full Hierarchy
        print("\n[2/5] Testing Full Hierarchy Endpoint (/api/study/hierarchy)...")
        h_res = client.get("/api/study/hierarchy?stage_id=stage_intermediate")
        assert h_res.status_code == 200, f"Hierarchy failed: {h_res.text}"
        hierarchy = h_res.json()
        groups = hierarchy.get("groups", [])
        print(f"  ✓ Intermediate Groups: {[g['code'] for g in groups]}")
        assert len(groups) >= 2
        
        # Verify papers and modules in Group 1
        g1_papers = groups[0].get("papers", [])
        print(f"  ✓ Group 1 Papers: {[p['name'] for p in g1_papers]}")
        assert len(g1_papers) >= 3

        # Verify chapters and topics in Paper 3 (Taxation)
        tax_paper = next((p for p in g1_papers if "Taxation" in p["name"]), None)
        assert tax_paper is not None, "Taxation paper missing"
        itc_ch = None
        for m in tax_paper.get("modules", []):
            for c in m.get("chapters", []):
                if "Input Tax Credit" in c["title"]:
                    itc_ch = c
                    break
        assert itc_ch is not None, "Input Tax Credit chapter missing in hierarchy"
        print(f"  ✓ Chapter found: {itc_ch['title']} (Topics: {len(itc_ch.get('topics', []))})")
        assert len(itc_ch.get("topics", [])) >= 2

        # 3. Chapter & Topic Progress Updates
        print("\n[3/5] Testing Chapter & Topic Progress Updates...")
        update_ch_res = client.patch(f"/api/study/ca-chapters/{itc_ch['id']}", json={
            "status": "in_progress",
            "confidence_score": 2,
            "weak_areas": "Motor vehicle seating capacity exceptions and gifts to employees",
            "notes": "Reviewed today with Sathi",
            "increment_revision": True
        })
        assert update_ch_res.status_code == 200, f"Chapter update failed: {update_ch_res.text}"
        print(f"  ✓ Updated Chapter {itc_ch['id']} progress and revision count")

        # 4. Student-Aware Recommendations from SQLite
        print("\n[4/5] Testing Student-Aware Recommendations (/api/study/recommendations)...")
        recs_res = client.get("/api/study/recommendations?student_id=pooja")
        assert recs_res.status_code == 200, f"Recommendations failed: {recs_res.text}"
        recs = recs_res.json()
        active_chapters = recs.get("active_chapters", [])
        print(f"  ✓ Active/Struggle Chapters recommended: {[c['title'] for c in active_chapters]}")
        assert len(active_chapters) > 0
        priority_topics = recs.get("priority_topics", [])
        print(f"  ✓ Priority Topics (Low confidence): {[t['title'] for t in priority_topics]}")
        assert len(priority_topics) > 0

        # 5. "Ask Sathi" from Syllabus Context
        print("\n[5/5] Testing 'Ask Sathi' from Syllabus Context Injection...")
        study_context = {
            "stage": "CA Intermediate",
            "group": "Group 1",
            "paper": "Paper 2: Corporate and Other Laws",
            "module": "Module 1: Company Law",
            "chapter": "Audit and Auditors",
            "topic": "Appointment of Auditors",
            "statutory_section": "Section 139 Companies Act 2013"
        }
        chat_payload = {
            "message": "Let's study Appointment of Auditors. Explain who appoints the first auditor.",
            "study_context": study_context,
            "history": []
        }
        ask_res = client.post("/api/chat", json=chat_payload)
        assert ask_res.status_code == 200, f"Ask Sathi chat failed: {ask_res.text}"
        ask_data = ask_res.json()
        print(f"  ✓ Grounded Flag: {ask_data.get('is_rag_grounded')}")
        print(f"  ✓ Citations count: {len(ask_data.get('citations') or [])}")
        print(f"  ✓ Routing: {ask_data.get('routing')}")
        print(f"  ✓ Sathi Reply preview: {ask_data['reply'][:150]}...")
        assert "139" in ask_data['reply'] or "auditor" in ask_data['reply'].lower()
        assert ask_data.get('is_rag_grounded') is True

    print("\n" + "=" * 60)
    print("ALL STUDY CONTEXT & ASK SATHI TESTS PASSED!")
    print("=" * 60)

if __name__ == "__main__":
    test_study_context()
