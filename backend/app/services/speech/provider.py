"""Speech-to-text transcription provider abstraction for Case Notes.

Privacy-first architecture:
- External cloud speech APIs (Google, Azure, AWS, OpenAI) are strictly prohibited.
- Audio is processed in-memory and immediately discarded.
- Production default is DisabledSpeechTranscriptionProvider.
- FakeSpeechTranscriptionProvider is used for automated testing with synthetic transcripts.
"""

from __future__ import annotations

import abc

from app.core import Settings, get_settings


class SpeechTranscriptionError(Exception):
    """Base exception for speech-to-text transcription errors."""

    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class SpeechProviderUnavailableError(SpeechTranscriptionError):
    """Raised when speech transcription is disabled or no approved provider is configured."""

    def __init__(
        self,
        message: str = "Speech-to-text is unavailable until an approved transcription provider is configured.",
    ):
        super().__init__(
            code="SPEECH_PROVIDER_NOT_CONFIGURED",
            message=message,
            status_code=503,
        )


# Backward-compatible aliases
SpeechTranscriptionException = SpeechTranscriptionError
SpeechProviderUnavailableException = SpeechProviderUnavailableError


class SpeechTranscriptionProvider(abc.ABC):
    """Abstract base class for speech-to-text transcription providers."""

    @property
    @abc.abstractmethod
    def provider_id(self) -> str:
        """Unique identifier for this provider implementation."""
        pass

    @property
    @abc.abstractmethod
    def is_available(self) -> bool:
        """Return True if this provider is configured and available to transcribe."""
        pass

    @abc.abstractmethod
    async def transcribe(
        self,
        audio_bytes: bytes,
        content_type: str,
        language: str = "en",
    ) -> str:
        """Transcribe audio bytes to text narrative.

        Args:
            audio_bytes: Raw binary audio in memory.
            content_type: MIME type of audio (e.g. audio/webm, audio/ogg, audio/wav).
            language: Target language code (default 'en').

        Returns:
            Transcribed text.

        Raises:
            SpeechTranscriptionException: On transcription or configuration failure.
        """
        pass


class DisabledSpeechTranscriptionProvider(SpeechTranscriptionProvider):
    """Default provider when speech-to-text is disabled or unconfigured."""

    @property
    def provider_id(self) -> str:
        return "disabled"

    @property
    def is_available(self) -> bool:
        return False

    async def transcribe(
        self,
        audio_bytes: bytes,
        content_type: str,
        language: str = "en",
    ) -> str:
        raise SpeechProviderUnavailableException()


class FakeSpeechTranscriptionProvider(SpeechTranscriptionProvider):
    """Synthetic test provider used exclusively for automated testing and CI.

    Returns deterministic synthetic transcripts without contacting external services.
    """

    def __init__(self, default_transcript: str = "This is a synthetic test case note."):
        self._default_transcript = default_transcript

    @property
    def provider_id(self) -> str:
        return "fake"

    @property
    def is_available(self) -> bool:
        return True

    async def transcribe(
        self,
        audio_bytes: bytes,
        content_type: str,
        language: str = "en",
    ) -> str:
        if not audio_bytes:
            raise SpeechTranscriptionException(code="EMPTY_AUDIO", message="Audio payload is empty.", status_code=400)
        return self._default_transcript


class FutureLocalWhisperProvider(SpeechTranscriptionProvider):
    """Stub for future self-hosted transcription engine (e.g. faster-whisper on CRBCL infrastructure).

    Not initialized until an approved local model is provisioned in the hosting environment.
    """

    @property
    def provider_id(self) -> str:
        return "local"

    @property
    def is_available(self) -> bool:
        return False

    async def transcribe(
        self,
        audio_bytes: bytes,
        content_type: str,
        language: str = "en",
    ) -> str:
        raise SpeechProviderUnavailableException(
            "Local self-hosted speech model is not initialized in this environment."
        )


def get_speech_provider(settings: Settings | None = None) -> SpeechTranscriptionProvider:
    """Factory creating the configured SpeechTranscriptionProvider."""
    if settings is None:
        settings = get_settings()

    if not settings.speech_to_text_enabled:
        return DisabledSpeechTranscriptionProvider()

    provider_name = (settings.speech_provider or "disabled").lower().strip()
    if provider_name == "fake":
        return FakeSpeechTranscriptionProvider()
    elif provider_name == "local":
        return FutureLocalWhisperProvider()
    else:
        return DisabledSpeechTranscriptionProvider()
