"""Speech-to-text service orchestrating privacy-first audio transcription for Case Notes.

CRBCL Privacy Architecture:
- Zero retention: Raw audio buffers are processed in-memory and discarded immediately.
- Zero transcript persistence: Transcripts are returned directly to the staff member's browser draft.
- Transcribe != Save: Transcription never creates, updates, signs, or publishes a Case Note.
- Audit safety: Only non-narrative metadata (actor ID, case ID, file size, provider, outcome) is audited.
  Raw audio and transcript text are NEVER logged.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import AuditService
from app.core import Settings, get_settings
from app.models.user import User
from app.services.case_service import CaseService
from app.services.speech.provider import (
    SpeechProviderUnavailableException,
    SpeechTranscriptionException,
    get_speech_provider,
)

# Supported audio MIME types
ALLOWED_AUDIO_CONTENT_TYPES = {
    "audio/webm",
    "audio/ogg",
    "audio/wav",
    "audio/x-wav",
    "audio/wave",
    "audio/mp4",
    "audio/m4a",
    "audio/x-m4a",
    "audio/mpeg",
    "audio/mp3",
    "audio/aac",
}


class SpeechService:
    def __init__(self, db: AsyncSession, settings: Settings | None = None):
        self.db = db
        self.settings = settings or get_settings()
        self.case_service = CaseService(db)
        self.audit = AuditService(db)

    def is_speech_to_text_enabled(self) -> bool:
        """Check if speech-to-text functionality is enabled in configuration."""
        return bool(self.settings.speech_to_text_enabled)

    def get_status(self) -> dict[str, Any]:
        """Return operational readiness status of the speech-to-text system."""
        provider = get_speech_provider(self.settings)
        is_enabled = self.is_speech_to_text_enabled()
        is_available = is_enabled and provider.is_available
        status_info = {
            "enabled": is_enabled,
            "provider": provider.provider_id,
            "available": is_available,
            "model": getattr(self.settings, "speech_model", "tiny"),
            "readiness": "ready" if is_available else ("disabled" if not is_enabled else "not_configured"),
            "max_file_size_bytes": self.settings.speech_max_file_size_bytes,
        }
        if hasattr(provider, "get_readiness_info"):
            readiness_meta = provider.get_readiness_info()
            status_info["model_loaded"] = readiness_meta.get("loaded", False)
        return status_info

    async def transcribe_case_note_audio(
        self,
        case_id: uuid.UUID,
        audio_bytes: bytes,
        content_type: str,
        current_user: User,
        language: str = "en",
        purpose: str = "case_note",
        note_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """Transcribe in-memory audio for use as draft assistance in a Case Note or Addendum.

        Enforces:
        - Case existence and case-level conflict-of-interest restriction checks
        - Speech-to-text feature toggle check
        - Provider readiness check
        - Audio validation (non-empty, size within technical limit, approved MIME type)
        - Metadata-only audit logging (no audio, no transcript content persisted)
        """
        # 1. Authorization & Case Validation
        await self.case_service.get_case_or_404(case_id, current_user)

        # 2. Feature Enabled Check
        if not self.is_speech_to_text_enabled():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": {
                        "code": "SPEECH_TRANSCRIPTION_DISABLED",
                        "message": "Speech-to-text is unavailable until an approved transcription provider is configured.",
                    }
                },
            )

        provider = get_speech_provider(self.settings)
        if not provider.is_available:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": {
                        "code": "SPEECH_PROVIDER_NOT_CONFIGURED",
                        "message": "Speech-to-text is unavailable until an approved transcription provider is configured.",
                    }
                },
            )

        # 3. Audio Validation
        if not audio_bytes or len(audio_bytes) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "EMPTY_AUDIO", "message": "Audio recording buffer is empty."}},
            )

        max_size = self.settings.speech_max_file_size_bytes
        if len(audio_bytes) > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail={
                    "error": {
                        "code": "AUDIO_TOO_LARGE",
                        "message": f"Audio file exceeds technical limit of {max_size // (1024 * 1024)} MB.",
                    }
                },
            )

        # Normalize content type (strip options like codecs=opus)
        normalized_content_type = content_type.split(";")[0].strip().lower() if content_type else ""
        if normalized_content_type not in ALLOWED_AUDIO_CONTENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail={
                    "error": {
                        "code": "UNSUPPORTED_AUDIO_FORMAT",
                        "message": f"Audio content type '{content_type}' is not supported. Supported formats include WebM, WAV, Ogg, and MP4.",
                    }
                },
            )

        # 4. In-Memory Transcription Execution
        try:
            transcript = await provider.transcribe(
                audio_bytes=audio_bytes,
                content_type=normalized_content_type,
                language=language,
            )
        except SpeechProviderUnavailableException as exc:
            raise HTTPException(
                status_code=exc.status_code,
                detail={"error": {"code": exc.code, "message": exc.message}},
            ) from exc
        except SpeechTranscriptionException as exc:
            raise HTTPException(
                status_code=exc.status_code,
                detail={"error": {"code": exc.code, "message": exc.message}},
            ) from exc
        except Exception as exc:
            # Audit failure metadata
            fail_metadata = {
                "provider": provider.provider_id,
                "content_type": normalized_content_type,
                "audio_bytes_length": len(audio_bytes),
                "outcome": "failed",
                "purpose": purpose,
            }
            if note_id:
                fail_metadata["note_id"] = str(note_id)

            await self.audit.log_event(
                event_type="speech_transcription_failed",
                user_id=current_user.id,
                entity_type="case",
                entity_id=case_id,
                metadata=fail_metadata,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": {"code": "TRANSCRIPTION_FAILED", "message": "Failed to transcribe audio."}},
            ) from exc

        # 5. Metadata-Only Audit Log (Strict Privacy: NO audio, NO transcript persisted)
        success_metadata = {
            "provider": provider.provider_id,
            "content_type": normalized_content_type,
            "audio_bytes_length": len(audio_bytes),
            "outcome": "success",
            "purpose": purpose,
        }
        if note_id:
            success_metadata["note_id"] = str(note_id)

        await self.audit.log_event(
            event_type="speech_transcription_succeeded",
            user_id=current_user.id,
            entity_type="case",
            entity_id=case_id,
            metadata=success_metadata,
        )

        return {
            "transcript": transcript,
            "provider": provider.provider_id,
            "language": language,
        }
