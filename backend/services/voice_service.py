# [FUTURE] Voice Service

# Planned: Whisper ASR + EdgeTTS / CosyVoice
# When ready, implement this class and wire to /api/v1/voice/* routes

class VoiceService:
    """Voice interaction service — stub for future development."""

    def __init__(self):
        self.asr_model = None  # Future: whisper model
        self.tts_engine = None  # Future: EdgeTTS / CosyVoice

    async def speech_to_text(self, audio_bytes: bytes) -> str:
        """[FUTURE] Convert speech audio to text using Whisper ASR."""
        raise NotImplementedError("Voice ASR is not yet implemented")

    async def text_to_speech(self, text: str, voice: str = "default") -> bytes:
        """[FUTURE] Convert text to speech audio using TTS engine."""
        raise NotImplementedError("Voice TTS is not yet implemented")

    async def is_available(self) -> bool:
        """Check if voice service is ready."""
        return False


voice_service = VoiceService()
