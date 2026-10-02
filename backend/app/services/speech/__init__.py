"""Speech-to-text service module for CRBCL Case Notes."""

from app.services.speech.provider import (
    DisabledSpeechTranscriptionProvider,
    FakeSpeechTranscriptionProvider,
    FutureLocalWhisperProvider,
    SpeechProviderUnavailableException,
    SpeechTranscriptionException,
    SpeechTranscriptionProvider,
    get_speech_provider,
)

__all__ = [
    "DisabledSpeechTranscriptionProvider",
    "FakeSpeechTranscriptionProvider",
    "FutureLocalWhisperProvider",
    "SpeechProviderUnavailableException",
    "SpeechTranscriptionException",
    "SpeechTranscriptionProvider",
    "get_speech_provider",
]
