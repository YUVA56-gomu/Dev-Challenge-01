import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import httpx
from app.core.memory.memory_provider import (
    LocalMemoryProvider,
    BackboardMemoryProvider,
    get_memory_provider
)


BASE_URL = "http://127.0.0.1:8000"

def test_memory_layer():
    print("=" * 60)
    print("SATHI CA COMPANION - PHASE 2 MEMORY VERIFICATION SUITE")
    print("=" * 60)

    # 1. LocalMemoryProvider Unit Tests
    print("\n[1/4] Testing LocalMemoryProvider (Default Local-First)...")
    local_mem = LocalMemoryProvider()
    mem_id = local_mem.save_memory("pooja", "Student prefers step-by-step numerical examples for costing formulas.", "preference")
    assert mem_id.startswith("mem_"), f"Invalid memory ID: {mem_id}"
    print(f"  ✓ Saved memory with ID: {mem_id}")

    retrieved = local_mem.retrieve_memory("pooja", query="costing")
    assert len(retrieved) > 0, "Failed to retrieve saved memory"
    print(f"  ✓ Retrieved {len(retrieved)} memory entries matching 'costing'")
    print(f"  ✓ Memory text: '{retrieved[0]['memory_text']}'")

    summary = local_mem.summarize_memory("pooja")
    assert len(summary) > 0, "Summary should not be empty"
    print(f"  ✓ Summary snippet:\n{summary[:160]}...")

    deleted = local_mem.delete_memory(mem_id)
    assert deleted is True, "Failed to delete memory"
    print(f"  ✓ Successfully deleted temporary memory: {mem_id}")

    # 2. BackboardMemoryProvider Graceful Fallback
    print("\n[2/4] Testing BackboardMemoryProvider Adapter & Fallback...")
    bb_provider = BackboardMemoryProvider(api_key="mock_invalid_key_test", local_fallback=local_mem)
    # When Backboard cloud fails or is unreachable, fallback should store in local SQLite smoothly
    fb_mem_id = bb_provider.save_memory("pooja", "Fallback memory persistence test", "test")
    assert fb_mem_id is not None
    print(f"  ✓ Backboard failure gracefully fell back to local store: {fb_mem_id}")
    local_mem.delete_memory(fb_mem_id)

    # 3. Provider Factory Pattern
    print("\n[3/4] Testing Memory Provider Factory Pattern...")
    active_provider = get_memory_provider()
    print(f"  ✓ Active default provider: {active_provider.__class__.__name__}")
    assert isinstance(active_provider, (LocalMemoryProvider, BackboardMemoryProvider))

    # 4. HTTP API Endpoints for Memory Profile
    print("\n[4/4] Testing HTTP Memory Profile Endpoints (/api/memory)...")
    with httpx.Client(base_url=BASE_URL, timeout=15.0) as client:
        profile_res = client.get("/api/memory/profile?student_id=pooja")
        assert profile_res.status_code == 200, f"Failed: {profile_res.text}"
        data = profile_res.json()
        print(f"  ✓ Student ID: {data['student_id']}")
        print(f"  ✓ Memory Provider in API: {data['provider']}")
        print(f"  ✓ Stored Memories Count: {len(data['memories'])}")
        assert len(data['memories']) > 0

        # Test adding a memory via API
        add_res = client.post("/api/memory", json={
            "student_id": "pooja",
            "memory_text": "Student prefers revising early in the morning before 8 AM.",
            "memory_type": "habit"
        })
        assert add_res.status_code == 200, f"Add memory failed: {add_res.text}"
        new_id = add_res.json().get("memory_id")
        print(f"  ✓ Added memory via API: {new_id}")
        local_mem.delete_memory(new_id)

    print("\n" + "=" * 60)
    print("ALL MEMORY VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    test_memory_layer()
