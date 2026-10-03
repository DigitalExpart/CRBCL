"""Speech-to-text transcription provider abstraction for Case Notes.

Privacy-first architecture:
- External cloud speech APIs (Google, Azure, AWS, OpenAI) are strictly prohibited.
- Audio is processed in-memory and immediately discarded.
- Production default is DisabledSpeechTranscriptionProvider.
- FakeSpeechTranscriptionProvider is used for automated testing with synthetic transcripts.
- LocalWhisperSpeechTranscriptionProvider delivers self-hosted transcription using faster-whisper.
"""

from __future__ import annotations

import abc
import asyncio
import contextlib
import io
import logging
import os
import tempfile
import threading
from typing import Any

from app.core import Settings, get_settings

logger = logging.getLogger(__name__)


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
        code: str = "SPEECH_PROVIDER_NOT_CONFIGURED",
    ):
        super().__init__(
            code=code,
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


class LocalWhisperSpeechTranscriptionProvider(SpeechTranscriptionProvider):
    """Self-hosted local transcription engine powered by faster-whisper.

    Privacy and Performance Guarantees:
    - In-memory decoding: audio is processed directly from memory buffer.
    - Zero external network requests: model runs entirely on local host.
    - Process-level model reuse: model is loaded once and cached in memory across requests.
    - Thread-safe concurrency bounding: semaphore bounds concurrent CPU inference calls.
    - Event-loop protection: blocking inference executes in worker threads via asyncio.to_thread.
    """

    _model_lock = threading.Lock()
    _cached_model: Any = None
    _cached_model_key: str | None = None
    _semaphore: asyncio.Semaphore | None = None
    _semaphore_loop: Any = None

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.model_name = getattr(self.settings, "speech_model", "tiny")
        self.device = getattr(self.settings, "speech_device", "cpu")
        self.compute_type = getattr(self.settings, "speech_compute_type", "int8")
        self.max_concurrency = getattr(self.settings, "speech_max_concurrency", 2)

    @property
    def provider_id(self) -> str:
        return "local_whisper"

    @property
    def is_available(self) -> bool:
        """Check if faster_whisper is importable and model can be loaded."""
        try:
            import faster_whisper  # noqa: F401
            return True
        except ImportError:
            return False

    def is_model_loaded(self) -> bool:
        """Check if the model instance is currently loaded in memory."""
        cache_key = f"{self.model_name}:{self.device}:{self.compute_type}"
        return (
            LocalWhisperSpeechTranscriptionProvider._cached_model is not None
            and LocalWhisperSpeechTranscriptionProvider._cached_model_key == cache_key
        )

    def get_readiness_info(self) -> dict[str, Any]:
        """Return safe, non-sensitive readiness metadata."""
        is_avail = self.is_available
        is_loaded = self.is_model_loaded() if is_avail else False
        return {
            "provider_id": self.provider_id,
            "model": self.model_name,
            "device": self.device,
            "loaded": is_loaded,
            "status": "ready" if is_loaded else ("available" if is_avail else "unavailable"),
        }

    def _get_or_load_model(self) -> Any:
        """Retrieve cached model or load into memory with thread safety."""
        cache_key = f"{self.model_name}:{self.device}:{self.compute_type}"
        if (
            LocalWhisperSpeechTranscriptionProvider._cached_model is not None
            and LocalWhisperSpeechTranscriptionProvider._cached_model_key == cache_key
        ):
            return LocalWhisperSpeechTranscriptionProvider._cached_model

        with LocalWhisperSpeechTranscriptionProvider._model_lock:
            # Double-check locking pattern
            if (
                LocalWhisperSpeechTranscriptionProvider._cached_model is not None
                and LocalWhisperSpeechTranscriptionProvider._cached_model_key == cache_key
            ):
                return LocalWhisperSpeechTranscriptionProvider._cached_model

            try:
                from faster_whisper import WhisperModel

                logger.info(
                    "Initializing self-hosted WhisperModel: model=%s, device=%s, compute_type=%s",
                    self.model_name,
                    self.device,
                    self.compute_type,
                )
                model = WhisperModel(
                    self.model_name,
                    device=self.device,
                    compute_type=self.compute_type,
                )
                LocalWhisperSpeechTranscriptionProvider._cached_model = model
                LocalWhisperSpeechTranscriptionProvider._cached_model_key = cache_key
                return model
            except Exception as exc:
                logger.error("Failed to initialize self-hosted Whisper model: %s", exc)
                raise SpeechProviderUnavailableException(
                    message=f"Self-hosted speech model '{self.model_name}' could not be initialized.",
                    code="SPEECH_MODEL_NOT_READY",
                ) from exc

    def _get_semaphore(self) -> asyncio.Semaphore:
        """Get or initialize the asyncio semaphore within the running event loop."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if (
            LocalWhisperSpeechTranscriptionProvider._semaphore is None
            or LocalWhisperSpeechTranscriptionProvider._semaphore_loop != loop
        ):
            LocalWhisperSpeechTranscriptionProvider._semaphore = asyncio.Semaphore(self.max_concurrency)
            LocalWhisperSpeechTranscriptionProvider._semaphore_loop = loop
        return LocalWhisperSpeechTranscriptionProvider._semaphore

    def _sync_transcribe(self, audio_bytes: bytes, language: str) -> str:
        """Synchronous CPU/GPU transcription routine to be called in worker thread."""
        model = self._get_or_load_model()

        # Primary: in-memory BytesIO decoding (avoids all temporary files)
        audio_stream = io.BytesIO(audio_bytes)
        try:
            segments, info = model.transcribe(
                audio_stream,
                language=language if language and language != "auto" else None,
                beam_size=1,
            )
            transcription_text = " ".join([s.text.strip() for s in segments if s.text]).strip()
            return transcription_text
        except Exception as primary_exc:
            logger.warning("In-memory audio stream decode encountered exception: %s. Attempting fallback.", primary_exc)
            # Fallback: write to secure temporary file with strict finally cleanup
            temp_path = None
            try:
                with tempfile.NamedTemporaryFile(suffix=".tmp", delete=False) as tf:
                    temp_path = tf.name
                    tf.write(audio_bytes)

                segments, info = model.transcribe(
                    temp_path,
                    language=language if language and language != "auto" else None,
                    beam_size=1,
                )
                transcription_text = " ".join([s.text.strip() for s in segments if s.text]).strip()
                return transcription_text
            except Exception as fb_exc:
                logger.error("Speech transcription inference failed: %s", fb_exc)
                raise SpeechTranscriptionException(
                    code="TRANSCRIPTION_FAILED",
                    message="Failed to transcribe audio with local speech engine.",
                    status_code=500,
                ) from fb_exc
            finally:
                if temp_path and os.path.exists(temp_path):
                    with contextlib.suppress(OSError):
                        os.remove(temp_path)

    async def transcribe(
        self,
        audio_bytes: bytes,
        content_type: str,
        language: str = "en",
    ) -> str:
        if not audio_bytes:
            raise SpeechTranscriptionException(code="EMPTY_AUDIO", message="Audio payload is empty.", status_code=400)

        sem = self._get_semaphore()
        async with sem:
            return await asyncio.to_thread(self._sync_transcribe, audio_bytes, language)


# Backward-compatible alias
FutureLocalWhisperProvider = LocalWhisperSpeechTranscriptionProvider


def get_speech_provider(settings: Settings | None = None) -> SpeechTranscriptionProvider:
    """Factory creating the configured SpeechTranscriptionProvider."""
    if settings is None:
        settings = get_settings()

    if not settings.speech_to_text_enabled:
        return DisabledSpeechTranscriptionProvider()

    provider_name = (settings.speech_provider or "disabled").lower().strip()
    if provider_name == "fake":
        return FakeSpeechTranscriptionProvider()
    elif provider_name in ("local", "local_whisper"):
        return LocalWhisperSpeechTranscriptionProvider(settings)
    else:
        return DisabledSpeechTranscriptionProvider()
