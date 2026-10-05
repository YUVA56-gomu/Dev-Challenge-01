import httpx
from abc import ABC, abstractmethod
from typing import Optional, List, Dict
from app.core.config import settings

class AIProvider(ABC):
    """
    Abstract Base Class for AI inference providers.
    Decouples the application logic from specific model hosting solutions
    (Ollama, local vLLM, hosted endpoints, etc.).
    """

    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None) -> str:
        """Generates a text completion for a multi-turn conversation."""
        pass

    @abstractmethod
    async def chat_stream(self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None):
        """Yields text chunks for a multi-turn conversation."""
        pass

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Single-turn helper for backward compatibility."""
        return await self.chat([{"role": "user", "content": prompt}], system_prompt=system_prompt)

    @abstractmethod
    async def check_health(self) -> dict:
        """Verifies connectivity to the underlying model provider."""
        pass

class OllamaGemmaProvider(AIProvider):
    """
    Concrete implementation of AIProvider interfacing with a local Ollama instance
    running Google's open-weight Gemma model.
    """

    def __init__(self, base_url: str = settings.OLLAMA_BASE_URL, model: str = settings.OLLAMA_MODEL):
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def check_health(self) -> dict:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    models = [m.get("name") for m in res.json().get("models", [])]
                    is_model_present = any(self.model in m for m in models)
                    return {
                        "connected": True,
                        "model_target": self.model,
                        "model_available": is_model_present,
                        "installed_models": models,
                    }
                return {
                    "connected": False,
                    "error": f"Ollama returned HTTP {res.status_code}",
                }
        except Exception as e:
            return {
                "connected": False,
                "error": f"Cannot reach Ollama at {self.base_url}: {str(e)}",
            }

    async def chat(self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None) -> str:
        formatted_messages = []
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})
        
        for msg in messages:
            # Ensure proper roles ('user', 'assistant')
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if content.strip():
                formatted_messages.append({"role": role, "content": content})

        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                )
                if response.status_code != 200:
                    raise RuntimeError(
                        f"Ollama API error ({response.status_code}): {response.text}"
                    )
                data = response.json()
                return data.get("message", {}).get("content", "").strip()
        except httpx.ConnectError:
            raise RuntimeError(
                f"Could not connect to Ollama at {self.base_url}. Is Ollama running?"
            )
        except Exception as e:
            raise RuntimeError(f"Gemma inference error: {str(e)}")

    async def chat_stream(self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None):
        formatted_messages = []
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if content.strip():
                formatted_messages.append({"role": role, "content": content})

        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "stream": True,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
            },
        }

        import json
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream("POST", f"{self.base_url}/api/chat", json=payload) as response:
                    if response.status_code != 200:
                        yield f"Ollama API error ({response.status_code})"
                        return
                    async for line in response.aiter_lines():
                        if line:
                            try:
                                chunk = json.loads(line)
                                if "message" in chunk and "content" in chunk["message"]:
                                    yield chunk["message"]["content"]
                            except json.JSONDecodeError:
                                pass
        except Exception as e:
            yield f"\n[Connection Error: {str(e)}]"

# Provider instance factory
_provider_instance: Optional[AIProvider] = None

def get_ai_provider() -> AIProvider:
    global _provider_instance
    if _provider_instance is None:
        _provider_instance = OllamaGemmaProvider()
    return _provider_instance
