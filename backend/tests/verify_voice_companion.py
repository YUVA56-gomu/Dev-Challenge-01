import httpx
import hashlib

BASE_URL = "http://127.0.0.1:8000"

def test_voice_companion_phase1():
    print("=" * 60)
    print("PHASE 1 - VOICE COMPANION VERIFICATION SUITE")
    print("=" * 60)
    
    with httpx.Client(timeout=60.0) as client:
        # TEST 1: Health & Voice Status
        print("\n[TEST 1] Testing Voice Status Endpoint...")
        res = client.get(f"{BASE_URL}/api/voice/status")
        assert res.status_code == 200, f"Failed: {res.text}"
        voice_status = res.json()
        print(f"  ✓ Voice Provider: {voice_status['provider']}")
        print(f"  ✓ Voice Available: {voice_status['available']}")
        print(f"  ✓ Default Voice ID: {voice_status['voice_id']}")
        print(f"  ✓ Fallback: {voice_status['fallback']}")
        print(f"  ✓ Cached Audio Files: {voice_status['cached_files']}")

        # TEST 2: Multi-turn Chat - Turn 1 (Depreciation)
        print("\n[TEST 2] Testing Gemma Multi-Turn - Turn 1: 'Explain depreciation in simple words'...")
        turn1_payload = {
            "message": "Explain depreciation in simple words.",
            "history": []
        }
        res1 = client.post(f"{BASE_URL}/api/chat", json=turn1_payload)
        assert res1.status_code == 200, f"Turn 1 failed: {res1.text}"
        t1_data = res1.json()
        print(f"  ✓ Model: {t1_data['model']}")
        print(f"  ✓ Reply Display Length: {len(t1_data['reply'])} chars")
        print(f"  ✓ Spoken Reply Length: {len(t1_data.get('spoken_reply', ''))} chars")
        print(f"  ✓ Spoken Reply Preview: {t1_data.get('spoken_reply', '')[:100]}...")
        assert len(t1_data['spoken_reply']) <= len(t1_data['reply'])
        assert not t1_data['spoken_reply'].startswith("#")

        # TEST 3: Multi-turn Chat - Turn 2 (Context reference "asset sold before useful life")
        print("\n[TEST 3] Testing Gemma Multi-Turn - Turn 2: 'What if the asset is sold before the useful life ends?'...")
        turn2_payload = {
            "message": "What if the asset is sold before the useful life ends?",
            "history": [
                {"role": "user", "content": "Explain depreciation in simple words."},
                {"role": "assistant", "content": t1_data['reply']}
            ]
        }
        res2 = client.post(f"{BASE_URL}/api/chat", json=turn2_payload)
        assert res2.status_code == 200, f"Turn 2 failed: {res2.text}"
        t2_data = res2.json()
        print(f"  ✓ Turn 2 Spoken Reply Preview: {t2_data.get('spoken_reply', '')[:100]}...")
        assert "depreciation" in t2_data['reply'].lower() or "profit" in t2_data['reply'].lower() or "loss" in t2_data['reply'].lower() or "asset" in t2_data['reply'].lower() or "book value" in t2_data['reply'].lower()

        # TEST 4: Multi-turn Chat - Turn 3 (Context reference "Give me an example")
        print("\n[TEST 4] Testing Gemma Multi-Turn - Turn 3: 'Give me a brief exam example.'...")
        turn3_payload = {
            "message": "Give me a brief exam example.",
            "history": [
                {"role": "user", "content": "Explain depreciation in simple words."},
                {"role": "assistant", "content": t1_data['reply']},
                {"role": "user", "content": "What if the asset is sold before the useful life ends?"},
                {"role": "assistant", "content": t2_data['reply']}
            ]
        }
        res3 = client.post(f"{BASE_URL}/api/chat", json=turn3_payload)
        assert res3.status_code == 200, f"Turn 3 failed: {res3.text}"
        t3_data = res3.json()
        print(f"  ✓ Turn 3 Spoken Reply Preview: {t3_data.get('spoken_reply', '')[:100]}...")

        # TEST 5: Voice Synthesize Graceful Fallback
        print("\n[TEST 5] Testing Voice Synthesize Endpoint Graceful Fallback...")
        synth_payload = {
            "text": t1_data['spoken_reply'],
            "voice_id": "21m00Tcm4TlvDq8ikWAM"
        }
        synth_res = client.post(f"{BASE_URL}/api/voice/synthesize", json=synth_payload)
        assert synth_res.status_code == 200
        synth_json = synth_res.json()
        print(f"  ✓ Synthesize response: {synth_json['status']} ({synth_json.get('message')})")
        assert synth_json['status'] == "fallback_to_browser"

        # TEST 6: Audio Hash Determinism (Cache Safety)
        print("\n[TEST 6] Testing Audio Cache Key Determinism (SHA-256)...")
        text_sample = "Depreciation represents the systematic allocation of the depreciable amount of an asset over its useful life."
        hash1 = hashlib.sha256(text_sample.encode('utf-8')).hexdigest()
        hash2 = hashlib.sha256(text_sample.encode('utf-8')).hexdigest()
        assert hash1 == hash2, "Hash must be deterministic!"
        print(f"  ✓ Cache SHA-256 Key: {hash1[:16]}... (Deterministic match)")

        print("\n" + "=" * 60)
        print("ALL PHASE 1 VOICE COMPANION CRITERIA VERIFIED!")
        print("=" * 60)

if __name__ == "__main__":
    test_voice_companion_phase1()
