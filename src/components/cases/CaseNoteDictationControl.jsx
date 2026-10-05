import React, { useCallback } from 'react';
import { caseNotesApi } from '@/api/caseNotes';
import SpeechDictationControl from '@/components/shared/SpeechDictationControl';

/**
 * CaseNoteDictationControl
 *
 * Privacy-first speech-to-text dictation input assistant for CRBCL Case Notes.
 *
 * Safety & Privacy Architecture:
 * 1. Audio is recorded locally in-memory via standard MediaRecorder (no third-party cloud SDKs).
 * 2. Audio is dispatched strictly to the authenticated CRBCL backend transcription endpoint.
 * 3. On success, the transcript is passed to onTranscriptReady for insertion/appending to the note draft.
 * 4. Cancel or error paths NEVER alter or clear the existing note draft.
 * 5. TRANSCRIBE != SAVE: Dictation does not automatically save, sign, or finalize the case note.
 */
export default function CaseNoteDictationControl({
  caseId,
  onTranscriptReady,
  disabled = false,
  language = 'en',
  purpose = 'case_note',
  noteId = null,
}) {
  const getStatus = useCallback(() => {
    if (!caseId) return Promise.resolve(null);
    return caseNotesApi.getTranscriptionStatus(caseId);
  }, [caseId]);

  const onTranscribe = useCallback(
    (audioBlob) => {
      return caseNotesApi.transcribeAudio(caseId, audioBlob, language, {
        purpose,
        noteId,
      });
    },
    [caseId, language, purpose, noteId]
  );

  return (
    <SpeechDictationControl
      getStatus={getStatus}
      onTranscribe={onTranscribe}
      onTranscriptReady={onTranscriptReady}
      disabled={disabled || !caseId}
      language={language}
      idleLabel="Dictate Note"
      idleTitle="Click to dictate case note. Audio is processed securely and appended to your draft."
      recordingLabel="Listening"
      processingLabel="Transcribing note…"
      successLabel="Transcript appended to draft"
      regionLabel="Speech-to-text case note dictation assistant"
    />
  );
}
