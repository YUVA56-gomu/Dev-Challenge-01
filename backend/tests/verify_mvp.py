import httpx

BASE_URL = "http://127.0.0.1:8000"

def test_all():
    print("=" * 60)
    print("SATHI CA COMPANION - MVP VERIFICATION SUITE")
    print("=" * 60)
    
    with httpx.Client(timeout=60.0) as client:
        # 1. Health
        print("\n[1/7] Testing Health Endpoint...")
        res = client.get(f"{BASE_URL}/api/health")
        assert res.status_code == 200, f"Health failed: {res.text}"
        data = res.json()
        print(f"  ✓ Status: {data['status']}")
        print(f"  ✓ Model: {data['ai_provider']['model_target']}")
        print(f"  ✓ Connected: {data['ai_provider']['connected']}")
        print(f"  ✓ Voice Provider: {data['voice_provider']['provider']} (Available: {data['voice_provider']['available']})")

        # 2. Multi-turn AI Chat
        print("\n[2/7] Testing AI Companion Multi-Turn Conversation...")
        chat_payload = {
            "message": "Can you give me a simple mnemonic to remember this?",
            "history": [
                {"role": "user", "content": "What are the key elements of SA 200 overall objectives of an auditor?"},
                {"role": "assistant", "content": "SA 200 establishes the overall objectives: to obtain reasonable assurance that financial statements are free from material misstatement, and to report on financial statements."}
            ]
        }
        res = client.post(f"{BASE_URL}/api/chat", json=chat_payload)
        assert res.status_code == 200, f"Chat failed: {res.text}"
        chat_data = res.json()
        print(f"  ✓ Model: {chat_data['model']}")
        print(f"  ✓ Provider: {chat_data['provider']}")
        print(f"  ✓ Response preview: {chat_data['reply'][:120]}...")

        # 3. Voice Synthesis & Fallback
        print("\n[3/7] Testing Voice Synthesis & Fallback Adapter...")
        voice_res = client.post(
            f"{BASE_URL}/api/voice/synthesize",
            json={"text": "Hello, let us study Accounting Standards today."}
        )
        assert voice_res.status_code == 200, f"Voice synthesize failed: {voice_res.text}"
        if "audio" in voice_res.headers.get("content-type", ""):
            print("  ✓ ElevenLabs returned direct MP3 audio stream!")
        else:
            v_data = voice_res.json()
            print(f"  ✓ Graceful Fallback verified: {v_data.get('status')} - {v_data.get('message')}")

        # 4. Study Subjects & Chapters
        print("\n[4/7] Testing Study Subjects & Chapter Operations...")
        res = client.get(f"{BASE_URL}/api/study/subjects")
        assert res.status_code == 200
        subjects = res.json()
        print(f"  ✓ Loaded {len(subjects)} CA Papers/Subjects")

        # Update a chapter
        first_ch_id = subjects[0]['chapters'][0]['id']
        update_res = client.patch(
            f"{BASE_URL}/api/study/chapters/{first_ch_id}",
            json={"status": "completed", "notes": "Thoroughly revised on 3 Oct."}
        )
        assert update_res.status_code == 200
        print(f"  ✓ Updated chapter {first_ch_id} status and notes")

        # 5. Tasks Management
        print("\n[5/7] Testing Daily Study Tasks CRUD...")
        task_res = client.post(f"{BASE_URL}/api/study/tasks", json={"title": "Revise Schedule III balance sheet format"})
        assert task_res.status_code == 200
        new_task = task_res.json()
        print(f"  ✓ Created task: {new_task['id']} - {new_task['title']}")
        
        # Toggle
        toggle_res = client.patch(f"{BASE_URL}/api/study/tasks/{new_task['id']}/toggle")
        assert toggle_res.status_code == 200
        print(f"  ✓ Toggled task completion: completed = {toggle_res.json()['completed']}")

        # 6. Progress Metrics
        print("\n[6/7] Testing Progress & Streak Stats...")
        prog_res = client.get(f"{BASE_URL}/api/study/progress")
        assert prog_res.status_code == 200
        prog = prog_res.json()
        print(f"  ✓ Overall Progress: {prog['overall_progress_percentage']}%")
        print(f"  ✓ Streak: {prog['current_streak_days']} Day(s)")

        # 7. Negative Thought Reframer (Gemma)
        print("\n[7/7] Testing Negative Thought Reframing (Gemma AI)...")
        reframe_res = client.post(
            f"{BASE_URL}/api/wellness/reframe",
            json={"thought": "I made so many mistakes in mock test practical problems today. I feel like giving up."}
        )
        assert reframe_res.status_code == 200
        reframed = reframe_res.json()
        print(f"  ✓ Reframer model: {reframed['model']}")
        print(f"  ✓ Reframed perspective:\n    {reframed['reframed'][:160]}...")

    print("\n" + "=" * 60)
    print("ALL 7 TEST PHASES PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    test_all()
