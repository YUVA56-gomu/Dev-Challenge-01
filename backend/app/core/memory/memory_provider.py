import os
import uuid
from typing import List, Dict, Optional
from abc import ABC, abstractmethod
from app.db.database import get_connection

class MemoryProvider(ABC):
    """Abstract interface for student semantic and episodic memory."""

    @abstractmethod
    def save_memory(self, student_id: str, memory_text: str, memory_type: str = "preference") -> str:
        """Saves a semantic learning insight or preference."""
        pass

    @abstractmethod
    def retrieve_memory(self, student_id: str, query: Optional[str] = None, limit: int = 5) -> List[Dict]:
        """Retrieves relevant semantic memories for the student."""
        pass

    @abstractmethod
    def summarize_memory(self, student_id: str) -> str:
        """Returns a concise student profile summary to inject into companion context."""
        pass

    @abstractmethod
    def delete_memory(self, memory_id: str) -> bool:
        """Deletes a specific memory entry."""
        pass

class LocalMemoryProvider(MemoryProvider):
    """
    Default local-first semantic memory provider.
    Stores and retrieves memories entirely from local SQLite database (sathi.db).
    Guarantees 100% privacy: zero student learning history is transmitted off-device.
    """

    def save_memory(self, student_id: str, memory_text: str, memory_type: str = "preference") -> str:
        conn = get_connection()
        cursor = conn.cursor()
        mem_id = f"mem_{uuid.uuid4().hex[:8]}"
        cursor.execute("""
            INSERT INTO semantic_memories (id, student_id, memory_text, memory_type)
            VALUES (?, ?, ?, ?);
        """, (mem_id, student_id, memory_text.strip(), memory_type))
        conn.commit()
        conn.close()
        return mem_id

    def retrieve_memory(self, student_id: str, query: Optional[str] = None, limit: int = 5) -> List[Dict]:
        conn = get_connection()
        cursor = conn.cursor()
        if query:
            cursor.execute("""
                SELECT id, memory_text, memory_type, created_at
                FROM semantic_memories
                WHERE student_id = ? AND memory_text LIKE ?
                ORDER BY created_at DESC
                LIMIT ?;
            """, (student_id, f"%{query}%", limit))
        else:
            cursor.execute("""
                SELECT id, memory_text, memory_type, created_at
                FROM semantic_memories
                WHERE student_id = ?
                ORDER BY created_at DESC
                LIMIT ?;
            """, (student_id, limit))
        rows = cursor.fetchall()
        memories = [dict(r) for r in rows]
        conn.close()
        return memories

    def summarize_memory(self, student_id: str) -> str:
        memories = self.retrieve_memory(student_id, limit=6)
        if not memories:
            return "Student prefers clear conceptual explanations and structured study sessions."
        
        points = [f"- {m['memory_text']}" for m in memories]
        return "\n".join(points)

    def delete_memory(self, memory_id: str) -> bool:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM semantic_memories WHERE id = ?;", (memory_id,))
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return deleted

class BackboardMemoryProvider(MemoryProvider):
    """
    Optional external cloud semantic memory provider using Backboard.io.
    Activated ONLY when BACKBOARD_API_KEY environment variable is configured.
    Falls back gracefully to LocalMemoryProvider on network failure or missing key.

    Privacy trade-off:
    - Transmits student learning preferences and struggle topics to Backboard.io cloud.
    - Deterministic progress (syllabus completion, marks, tasks) always stays in local SQLite.
    """

    def __init__(self, api_key: str, local_fallback: LocalMemoryProvider):
        self.api_key = api_key
        self.fallback = local_fallback
        self.base_url = os.getenv("BACKBOARD_BASE_URL", "https://api.backboard.io/v1")

    def save_memory(self, student_id: str, memory_text: str, memory_type: str = "preference") -> str:
        try:
            import httpx
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            payload = {
                "user_id": student_id,
                "text": memory_text,
                "metadata": {"type": memory_type, "app": "Sathi"}
            }
            # Attempt Backboard API call with short timeout
            res = httpx.post(f"{self.base_url}/memories", headers=headers, json=payload, timeout=3.0)
            if res.status_code in [200, 201]:
                data = res.json()
                return data.get("id", f"bb_{uuid.uuid4().hex[:8]}")
        except Exception as e:
            print(f"[BackboardMemoryProvider] Call failed ({e}), using local fallback.")
        return self.fallback.save_memory(student_id, memory_text, memory_type)

    def retrieve_memory(self, student_id: str, query: Optional[str] = None, limit: int = 5) -> List[Dict]:
        try:
            import httpx
            headers = {"Authorization": f"Bearer {self.api_key}"}
            params = {"user_id": student_id, "limit": limit}
            if query:
                params["query"] = query
            res = httpx.get(f"{self.base_url}/memories", headers=headers, params=params, timeout=3.0)
            if res.status_code == 200:
                data = res.json()
                return [{"id": m.get("id"), "memory_text": m.get("text"), "memory_type": m.get("metadata", {}).get("type", "cloud")} for m in data.get("memories", [])]
        except Exception as e:
            print(f"[BackboardMemoryProvider] Retrieval failed ({e}), using local fallback.")
        return self.fallback.retrieve_memory(student_id, query, limit)

    def summarize_memory(self, student_id: str) -> str:
        return self.fallback.summarize_memory(student_id)

    def delete_memory(self, memory_id: str) -> bool:
        return self.fallback.delete_memory(memory_id)

_memory_provider_instance = None

def get_memory_provider() -> MemoryProvider:
    global _memory_provider_instance
    if _memory_provider_instance is None:
        local_provider = LocalMemoryProvider()
        api_key = os.getenv("BACKBOARD_API_KEY", "").strip()
        if api_key:
            _memory_provider_instance = BackboardMemoryProvider(api_key=api_key, local_fallback=local_provider)
        else:
            _memory_provider_instance = local_provider
    return _memory_provider_instance
