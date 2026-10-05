import sys
import os
import json

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app
from app.db.database import init_db
from app.repositories.practice_repository import PracticeRepository

def run_tests():
    print("=" * 60)
    print("SATHI CA COMPANION - PHASE 3 PRACTICE & EVALUATION SUITE")
    print("=" * 60)

    init_db()
    client = TestClient(app)

    # -------------------------------------------------------------
    # [1/8] Testing Question Retrieval & Source Provenance
    # -------------------------------------------------------------
    print("\n[1/8] Testing Question Retrieval & Source Provenance...")
    res = client.get("/api/practice/questions?paper_id=paper_tax")
    assert res.status_code == 200, f"Failed: {res.text}"
    questions = res.json()
    assert len(questions) >= 2, f"Expected at least 2 tax questions, got {len(questions)}"
    
    q_tax = questions[0]
    print(f"  ✓ Retrieved question: {q_tax['id']} ({q_tax['question_type']} - {q_tax['marks']} Marks)")
    print(f"  ✓ Source Verified: {q_tax['source']} (Page {q_tax.get('source_page')})")
    assert "ICAI" in q_tax["source"] or "Sathi" in q_tax["source"], "Source provenance missing"

    # -------------------------------------------------------------
    # [2/8] Testing Deterministic MCQ Evaluation
    # -------------------------------------------------------------
    print("\n[2/8] Testing Deterministic MCQ Evaluation...")
    # q_tax_sec17_5_mcq: "Up to 13 persons (including driver)"
    submit_mcq = {
        "question_id": "q_tax_sec17_5_mcq",
        "student_id": "pooja",
        "user_answer": "Up to 13 persons (including driver)",
        "time_spent_seconds": 45
    }
    res = client.post("/api/practice/submit", json=submit_mcq)
    assert res.status_code == 200, f"Submit MCQ failed: {res.text}"
    mcq_eval = res.json()
    assert mcq_eval["is_correct"] is True, f"Expected correct MCQ, got {mcq_eval}"
    assert mcq_eval["score"] == 2.0, f"Expected full 2.0 marks, got {mcq_eval['score']}"
    print(f"  ✓ MCQ Score: {mcq_eval['score']}/{mcq_eval['max_score']} (is_correct={mcq_eval['is_correct']})")
    print(f"  ✓ Spoken Feedback: {mcq_eval['evaluation']['spoken_explanation']}")

    # -------------------------------------------------------------
    # [3/8] Testing Theory / Practical Answer Submission & AI Marking
    # -------------------------------------------------------------
    print("\n[3/8] Testing Practical Answer Submission & Step Marking...")
    # Answer for q_tax_itc_1: intentionally partial answer missing insurance rule
    submit_theory = {
        "question_id": "q_tax_itc_1",
        "student_id": "pooja",
        "user_answer": (
            "Under Section 17(5) of the CGST Act 2017:\n"
            "1. For the motor car costing 12 lakhs, seating capacity is 5 persons which is less than 13 persons. So ITC is blocked.\n"
            "2. For the mini-bus, seating capacity is 22 persons which is greater than 13. So full ITC of 4,50,000 can be claimed.\n"
            "I am not sure about the car insurance."
        ),
        "time_spent_seconds": 210
    }
    res = client.post("/api/practice/submit", json=submit_theory)
    assert res.status_code == 200, f"Theory submission failed: {res.text}"
    theory_eval = res.json()
    assert theory_eval["attempt_id"], "Attempt ID missing"
    assert "evaluation" in theory_eval, "Evaluation payload missing"
    eval_data = theory_eval["evaluation"]
    
    print(f"  ✓ Score Awarded: {theory_eval['score']} / {theory_eval['max_score']}")
    print(f"  ✓ Strengths: {eval_data.get('strengths')}")
    print(f"  ✓ Identified Mistakes: {eval_data.get('mistakes')}")
    print(f"  ✓ Spoken Explanation Preview: {eval_data.get('spoken_explanation')[:90]}...")
    assert len(eval_data.get("strengths", [])) > 0 or len(eval_data.get("mistakes", [])) > 0

    # -------------------------------------------------------------
    # [4/8] Testing Weak Topic Detection & Topic Performance
    # -------------------------------------------------------------
    print("\n[4/8] Testing Weak Topic Detection & Performance Tracking...")
    res = client.get("/api/practice/weak-areas?student_id=pooja")
    assert res.status_code == 200, f"Failed weak areas: {res.text}"
    weak_areas = res.json()
    print(f"  ✓ Active Weak Areas Detected: {len(weak_areas)}")
    for wa in weak_areas[:2]:
        print(f"    - {wa.get('topic_title')} ({wa.get('chapter_title')}) | Accuracy: {wa.get('accuracy_pct')}%")

    # -------------------------------------------------------------
    # [5/8] Testing Spaced Revision Scheduling
    # -------------------------------------------------------------
    print("\n[5/8] Testing Spaced Revision Scheduling...")
    res = client.get("/api/practice/revisions?student_id=pooja")
    assert res.status_code == 200, f"Failed revisions: {res.text}"
    revisions = res.json()
    assert len(revisions) >= 1, "Expected scheduled revisions for student"
    rev_item = revisions[0]
    print(f"  ✓ Scheduled Revision: Topic '{rev_item.get('topic_title')}' (Interval Day {rev_item.get('interval_day')})")

    # Complete revision
    res_comp = client.post(f"/api/practice/revisions/{rev_item['id']}/complete")
    assert res_comp.status_code == 200, "Completing revision failed"
    print(f"  ✓ Completed revision task: {rev_item['id']}")

    # -------------------------------------------------------------
    # [6/8] Testing Practice Statistics Endpoint
    # -------------------------------------------------------------
    print("\n[6/8] Testing Practice Statistics Endpoint (/api/practice/stats)...")
    res = client.get("/api/practice/stats?student_id=pooja")
    assert res.status_code == 200, f"Stats failed: {res.text}"
    stats = res.json()
    print(f"  ✓ Questions Attempted: {stats['questions_attempted']}")
    print(f"  ✓ Questions Correct: {stats['questions_correct']}")
    print(f"  ✓ Overall Accuracy: {stats['accuracy_pct']}%")
    print(f"  ✓ Practice Streak: {stats['practice_streak']} Day(s)")
    assert stats["questions_attempted"] >= 2, "Expected at least 2 attempts registered"

    # -------------------------------------------------------------
    # [7/8] Testing Exam Mode Simulation & Submission
    # -------------------------------------------------------------
    print("\n[7/8] Testing Exam Mode Simulation & Automated Evaluation...")
    exam_req = {
        "student_id": "pooja",
        "paper_id": "paper_tax",
        "title": "Taxation GST Quick Test",
        "num_questions": 2,
        "time_limit_minutes": 20
    }
    res = client.post("/api/practice/exam/start", json=exam_req)
    assert res.status_code == 200, f"Start exam failed: {res.text}"
    exam_session = res.json()
    session_id = exam_session["session_id"]
    print(f"  ✓ Exam Session Started: {session_id} ({exam_session['total_questions']} Questions, {exam_session['total_marks']} Marks)")

    # Submit exam
    exam_submit_payload = {
        "answers": {
            exam_session["questions"][0]["id"]: "All passenger vehicles are blocked under Section 17(5).",
            exam_session["questions"][1]["id"]: "Up to 13 persons (including driver)"
        },
        "time_spent_seconds": 640
    }
    res_sub = client.post(f"/api/practice/exam/{session_id}/submit", json=exam_submit_payload)
    assert res_sub.status_code == 200, f"Exam submit failed: {res_sub.text}"
    exam_result = res_sub.json()
    print(f"  ✓ Exam Completed: Score {exam_result['score_obtained']}/{exam_result['total_marks']} (Accuracy {exam_result['accuracy_pct']}%)")
    print(f"  ✓ Recommended Steps: {exam_result['recommended_steps'][0]}")

    # -------------------------------------------------------------
    # [8/8] Testing 'Ask Sathi' from Practice Attempt Context Injection
    # -------------------------------------------------------------
    print("\n[8/8] Testing 'Ask Sathi' with Practice Attempt Context...")
    chat_req = {
        "message": "Why did I lose marks on the motor vehicle question?",
        "study_context": {
            "paper": "Paper 4: Taxation",
            "chapter": "Input Tax Credit",
            "topic": "Blocked Credits under Section 17(5)",
            "attempt_context": {
                "question_text": "Determine eligible ITC on director's car and mini-bus.",
                "user_answer": "I wasn't sure about the car insurance.",
                "score": 3.0,
                "max_score": 5.0,
                "mistakes": ["Omitted rule for general insurance on motor vehicles under Section 17(5)(ab)"],
                "missing_concepts": ["Section 17(5)(ab) ancillary service blocking"],
                "ideal_answer": "Insurance on blocked vehicles is also blocked under Section 17(5)(ab)."
            }
        }
    }
    res_chat = client.post("/api/chat", json=chat_req)
    assert res_chat.status_code == 200, f"Chat with attempt context failed: {res_chat.text}"
    chat_resp = res_chat.json()
    print(f"  ✓ Sathi Model: {chat_resp['model']}")
    print(f"  ✓ Grounded Flag: {chat_resp['is_rag_grounded']}")
    print(f"  ✓ Sathi Explanation Preview:\n    {chat_resp['reply'][:150]}...")
    assert "17(5)" in chat_resp["reply"] or "insurance" in chat_resp["reply"].lower()

    print("\n" + "=" * 60)
    print("ALL 8 PRACTICE & EVALUATION PHASES PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
