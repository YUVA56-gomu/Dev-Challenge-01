import os
import hashlib
import httpx
from abc import ABC, abstractmethod
from typing import Optional
from app.core.config import settings

class VoiceProvider(ABC):
    """
    Abstract Base Class for Text-to-Speech (TTS) services.
    Enables pluggable voice providers (ElevenLabs, local piper/whisper, or browser-native).
    """

    @abstractmethod
    async def synthesize(self, text: str, voice_id: Optional[str] = None) -> bytes:
        """Converts text to audio bytes (e.g. mp3)."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Checks if provider has required credentials/configuration."""
        pass


class ElevenLabsVoiceProvider(VoiceProvider):
    """
    ElevenLabs TTS implementation with disk-based caching to conserve credits.
    """

    def __init__(self, api_key: Optional[str] = settings.ELEVENLABS_API_KEY, default_voice_id: str = settings.ELEVENLABS_VOICE_ID):
        self.api_key = api_key
        self.default_voice_id = default_voice_id
        self.cache_dir = settings.AUDIO_CACHE_DIR
        os.makedirs(self.cache_dir, exist_ok=True)

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def _get_cache_path(self, text: str, voice_id: str) -> str:
        # Deterministic SHA-256 hash based on voice_id and normalized text
        normalized = text.strip()
        key = hashlib.sha256(f"{voice_id}_{normalized}".encode("utf-8")).hexdigest()
        return os.path.join(self.cache_dir, f"{key}.mp3")

    def get_cache_stats(self) -> dict:
        if not os.path.exists(self.cache_dir):
            return {"file_count": 0, "total_size_bytes": 0}
        files = [f for f in os.listdir(self.cache_dir) if f.endswith(".mp3")]
        total_size = sum(os.path.getsize(os.path.join(self.cache_dir, f)) for f in files)
        return {"file_count": len(files), "total_size_bytes": total_size}

    async def synthesize(self, text: str, voice_id: Optional[str] = None) -> bytes:
        if not self.is_available():
            return b""

        target_voice = voice_id or self.default_voice_id
        cache_path = self._get_cache_path(text, target_voice)

        # 1. Return cached audio if present (costs 0 credits!)
        if os.path.exists(cache_path):
            with open(cache_path, "rb") as f:
                return f.read()

        # 2. Call ElevenLabs API
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{target_voice}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key,
        }
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
            },
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(url, json=payload, headers=headers)
            if res.status_code == 200:
                audio_bytes = res.content
                # Save to disk cache for future replay
                try:
                    with open(cache_path, "wb") as f:
                        f.write(audio_bytes)
                except Exception as e:
                    print(f"Warning: could not write audio cache: {e}")
                return audio_bytes
            else:
                raise RuntimeError(f"ElevenLabs API error ({res.status_code}): {res.text}")


class NullVoiceProvider(VoiceProvider):
    """
    Default voice provider when cloud TTS credits or keys are not provided.
    Delegates vocal synthesis to client-side browser Web Speech API.
    """
    def is_available(self) -> bool:
        return False

    async def synthesize(self, text: str, voice_id: Optional[str] = None) -> bytes:
        return b""


# Factory
_voice_provider_instance: Optional[VoiceProvider] = None

def get_voice_provider() -> VoiceProvider:
    global _voice_provider_instance
    if _voice_provider_instance is None:
        if settings.ELEVENLABS_API_KEY:
            _voice_provider_instance = ElevenLabsVoiceProvider()
        else:
            _voice_provider_instance = NullVoiceProvider()
    return _voice_provider_instance
