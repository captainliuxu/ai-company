import json
import logging

import httpx

import backend.config as config

logger = logging.getLogger(__name__)

_MIME_EXTENSION_MAP = {
    "audio/mpeg": "mp3",
    "audio/mp3": "mp3",
    "audio/mp4": "mp4",
    "audio/m4a": "m4a",
    "audio/wav": "wav",
    "audio/x-wav": "wav",
    "audio/webm": "webm",
    "audio/ogg": "ogg",
    "audio/flac": "flac",
}


class VoiceServiceError(RuntimeError):
    """Raised when the voice provider request cannot be completed."""


class VoiceService:
    """Speech-to-text and text-to-speech service via OpenAI-compatible APIs."""

    def __init__(self):
        self.api_key = str(getattr(config, "VOICE_API_KEY", "")).strip()
        self.base_url = str(getattr(config, "VOICE_BASE_URL", "")).strip().rstrip("/")
        self.voice_enabled = bool(getattr(config, "VOICE_ENABLED", True))
        self.stt_model = str(getattr(config, "VOICE_STT_MODEL", "whisper-1"))
        self.tts_model = str(getattr(config, "VOICE_TTS_MODEL", "tts-1"))
        self.default_voice = str(getattr(config, "VOICE_TTS_VOICE", "nova"))
        self.max_upload_mb = int(getattr(config, "VOICE_MAX_UPLOAD_MB", 25))
        self._availability_error: str | None = None

    async def speech_to_text(self, audio_bytes: bytes, mime_type: str) -> str:
        """Convert speech audio to text using the configured provider."""
        self._ensure_ready("speech-to-text")
        if not self.stt_model:
            raise VoiceServiceError(
                "Speech-to-text is unavailable: VOICE_STT_MODEL is not configured"
            )
        if not audio_bytes:
            raise VoiceServiceError("Speech-to-text failed: audio payload is empty")

        max_upload_bytes = self.max_upload_mb * 1024 * 1024
        if len(audio_bytes) > max_upload_bytes:
            raise VoiceServiceError(
                f"Speech-to-text failed: audio payload exceeds {self.max_upload_mb} MB limit"
            )

        normalized_mime_type = self._normalize_mime_type(mime_type)
        filename = f"audio.{self._extension_for_mime(normalized_mime_type)}"

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
                response = await client.post(
                    self._endpoint("audio/transcriptions"),
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    data={"model": self.stt_model},
                    files={
                        "file": (filename, audio_bytes, normalized_mime_type),
                    },
                )
        except httpx.HTTPError as exc:
            raise VoiceServiceError(
                f"Speech-to-text provider request failed: {exc}"
            ) from exc

        if response.status_code >= 400:
            raise VoiceServiceError(
                "Speech-to-text provider returned "
                f"HTTP {response.status_code}: {self._response_error_text(response)}"
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise VoiceServiceError(
                "Speech-to-text provider returned invalid JSON response"
            ) from exc

        text = payload.get("text")
        if not isinstance(text, str) or not text.strip():
            raise VoiceServiceError(
                "Speech-to-text provider response did not include transcribed text"
            )
        return text.strip()

    async def text_to_speech(self, text: str, voice: str = "default") -> bytes:
        """Convert text to speech audio using the configured provider."""
        self._ensure_ready("text-to-speech")
        if not self.tts_model:
            raise VoiceServiceError(
                "Text-to-speech is unavailable: VOICE_TTS_MODEL is not configured"
            )
        if not text or not text.strip():
            raise VoiceServiceError("Text-to-speech failed: input text is empty")

        normalized_voice = (voice or "").strip()
        selected_voice = self.default_voice if normalized_voice == "default" else normalized_voice
        if not selected_voice:
            selected_voice = self.default_voice

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
                response = await client.post(
                    self._endpoint("audio/speech"),
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "content-type": "application/json",
                    },
                    json={
                        "model": self.tts_model,
                        "voice": selected_voice,
                        "input": text,
                    },
                )
        except httpx.HTTPError as exc:
            raise VoiceServiceError(
                f"Text-to-speech provider request failed: {exc}"
            ) from exc

        if response.status_code >= 400:
            raise VoiceServiceError(
                "Text-to-speech provider returned "
                f"HTTP {response.status_code}: {self._response_error_text(response)}"
            )

        content_type = response.headers.get("content-type", "").lower()
        if "application/json" in content_type:
            raise VoiceServiceError(
                "Text-to-speech provider returned JSON instead of audio: "
                f"{self._response_error_text(response)}"
            )

        audio_bytes = response.content
        if not audio_bytes:
            raise VoiceServiceError(
                "Text-to-speech provider returned an empty audio payload"
            )
        return audio_bytes

    async def is_available(self) -> bool:
        """Check whether the voice provider can be reached with current configuration."""
        if not self.voice_enabled:
            self._availability_error = "Voice service is disabled by configuration"
            return False

        if not self.api_key:
            self._availability_error = "VOICE_API_KEY is not configured"
            return False

        if not self.base_url:
            self._availability_error = "VOICE_BASE_URL is not configured"
            return False

        if not self.stt_model:
            self._availability_error = "VOICE_STT_MODEL is not configured"
            return False

        if not self.tts_model:
            self._availability_error = "VOICE_TTS_MODEL is not configured"
            return False

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
                response = await client.get(
                    self._endpoint("models"),
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
        except httpx.HTTPError as exc:
            self._availability_error = f"Voice provider health check failed: {exc}"
            logger.warning(self._availability_error)
            return False

        if response.status_code >= 400:
            self._availability_error = (
                "Voice provider health check returned "
                f"HTTP {response.status_code}: {self._response_error_text(response)}"
            )
            logger.warning(self._availability_error)
            return False

        self._availability_error = None
        return True

    @property
    def availability_error(self) -> str | None:
        return self._availability_error

    def _ensure_ready(self, operation: str) -> None:
        if not self.voice_enabled:
            raise VoiceServiceError(
                f"{operation.capitalize()} is unavailable: voice service is disabled by configuration"
            )
        if not self.api_key:
            raise VoiceServiceError(
                f"{operation.capitalize()} is unavailable: VOICE_API_KEY is not configured"
            )
        if not self.base_url:
            raise VoiceServiceError(
                f"{operation.capitalize()} is unavailable: VOICE_BASE_URL is not configured"
            )

    def _endpoint(self, path: str) -> str:
        normalized_path = path.lstrip("/")
        if self.base_url.endswith("/v1"):
            return f"{self.base_url}/{normalized_path}"
        return f"{self.base_url}/v1/{normalized_path}"

    def _normalize_mime_type(self, mime_type: str) -> str:
        normalized = (mime_type or "").strip().lower()
        if not normalized:
            return "application/octet-stream"
        return normalized.partition(";")[0].strip() or "application/octet-stream"

    def _extension_for_mime(self, mime_type: str) -> str:
        return _MIME_EXTENSION_MAP.get(self._normalize_mime_type(mime_type), "bin")

    def _response_error_text(self, response: httpx.Response) -> str:
        body_text = response.text.strip()
        if not body_text:
            return "empty error response"

        try:
            payload = json.loads(body_text)
        except ValueError:
            return body_text[:500]

        if isinstance(payload, dict):
            error = payload.get("error")
            if isinstance(error, dict):
                message = error.get("message")
                if isinstance(message, str) and message.strip():
                    return message.strip()[:500]
            message = payload.get("message")
            if isinstance(message, str) and message.strip():
                return message.strip()[:500]

        return body_text[:500]


voice_service = VoiceService()
