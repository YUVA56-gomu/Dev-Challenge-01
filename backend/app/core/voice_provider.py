from abc import ABC, abstractmethod
from typing import Optional

class VoiceProvider(ABC):
    """
    Abstract Base Class for Text-to-Speech (TTS) services.
    Enables pluggable voice providers (ElevenLabs, local piper/whisper, or browser-native).
    """

    @abstractmethod
    async def synthesize(self, text: str, voice_id: Optional[str] = None) -> bytes:
        """Converts text to audio bytes (e.g. mp3)."""
        pass

class NullVoiceProvider(VoiceProvider):
    """
    Default voice provider when cloud TTS credits or keys are not provided.
    Delegates vocal synthesis to client-side browser Web Speech API.
    """
    async def synthesize(self, text: str, voice_id: Optional[str] = None) -> bytes:
        return b""
