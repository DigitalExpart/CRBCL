import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Mic, Square, X, Loader2, Check, AlertCircle } from 'lucide-react';
import { caseNotesApi } from '@/api/caseNotes';

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
}) {
  const [status, setStatus] = useState('idle'); // idle | requesting | recording | processing | success | error
  const [errorMessage, setErrorMessage] = useState('');
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [isSupported, setIsSupported] = useState(true);

  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerIntervalRef = useRef(null);
  const isCancelledRef = useRef(false);

  // Check browser MediaRecorder / getUserMedia support
  useEffect(() => {
    const supported =
      typeof navigator !== 'undefined' &&
      !!navigator.mediaDevices?.getUserMedia &&
      typeof window.MediaRecorder !== 'undefined';
    setIsSupported(supported);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }
    };
  }, []);

  const formatTimer = (secs) => {
    const m = Math.floor(secs / 60)
      .toString()
      .padStart(2, '0');
    const s = (secs % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  const startRecording = async () => {
    if (!caseId) {
      setErrorMessage('Case identifier is missing.');
      setStatus('error');
      return;
    }

    setErrorMessage('');
    setStatus('requesting');
    isCancelledRef.current = false;

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      // Select supported audio MIME type
      let mimeType = 'audio/webm';
      if (!MediaRecorder.isTypeSupported('audio/webm')) {
        if (MediaRecorder.isTypeSupported('audio/ogg')) mimeType = 'audio/ogg';
        else if (MediaRecorder.isTypeSupported('audio/mp4')) mimeType = 'audio/mp4';
        else mimeType = ''; // Let browser use default
      }

      const recorder = mimeType
        ? new MediaRecorder(stream, { mimeType })
        : new MediaRecorder(stream);

      mediaRecorderRef.current = recorder;
      audioChunksRef.current = [];

      recorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      recorder.onstop = async () => {
        // Stop all audio hardware tracks
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((track) => track.stop());
          streamRef.current = null;
        }
        if (timerIntervalRef.current) {
          clearInterval(timerIntervalRef.current);
          timerIntervalRef.current = null;
        }

        // If cancelled by staff member, discard buffer and leave draft untouched
        if (isCancelledRef.current) {
          audioChunksRef.current = [];
          setStatus('idle');
          setRecordingSeconds(0);
          return;
        }

        const audioBlob = new Blob(audioChunksRef.current, {
          type: recorder.mimeType || 'audio/webm',
        });
        audioChunksRef.current = [];

        if (audioBlob.size === 0) {
          setErrorMessage('No audio captured. Please check microphone and try again.');
          setStatus('error');
          return;
        }

        setStatus('processing');
        try {
          const result = await caseNotesApi.transcribeAudio(caseId, audioBlob, language);
          if (result?.transcript && onTranscriptReady) {
            onTranscriptReady(result.transcript);
            setStatus('success');
            setTimeout(() => {
              setStatus('idle');
              setRecordingSeconds(0);
            }, 2500);
          } else {
            setStatus('idle');
          }
        } catch (err) {
          console.error('Speech transcription error:', err);
          const userMsg =
            err.message ||
            'Speech-to-text is unavailable until an approved transcription provider is configured.';
          setErrorMessage(userMsg);
          setStatus('error');
        }
      };

      recorder.start(250); // collect slices every 250ms
      setStatus('recording');
      setRecordingSeconds(0);

      timerIntervalRef.current = setInterval(() => {
        setRecordingSeconds((prev) => prev + 1);
      }, 1000);
    } catch (err) {
      console.warn('Microphone permission / initialization failed:', err);
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setErrorMessage('Microphone access was denied. Please allow microphone permissions in your browser.');
      } else {
        setErrorMessage('Unable to initialize microphone. Please check audio devices.');
      }
      setStatus('error');
    }
  };

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
  }, []);

  const cancelRecording = useCallback(() => {
    isCancelledRef.current = true;
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    } else {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      }
      if (timerIntervalRef.current) {
        clearInterval(timerIntervalRef.current);
        timerIntervalRef.current = null;
      }
      audioChunksRef.current = [];
      setStatus('idle');
      setRecordingSeconds(0);
    }
  }, []);

  if (!isSupported) {
    return (
      <span
        className="inline-flex items-center gap-1 text-[11px] text-muted-foreground bg-muted/60 px-2 py-0.5 rounded border border-border/40"
        title="Speech-to-text dictation is not supported in this browser version."
      >
        <Mic className="w-3 h-3 text-muted-foreground/60" />
        Dictation Unavailable
      </span>
    );
  }

  return (
    <div className="flex flex-col gap-1.5" role="region" aria-label="Speech-to-text case note dictation assistant">
      <div className="flex items-center gap-2">
        {/* State: Idle / Ready */}
        {status === 'idle' && (
          <button
            type="button"
            onClick={startRecording}
            disabled={disabled}
            aria-label="Dictate case note via microphone"
            title="Click to dictate case note. Audio is processed securely and appended to your draft."
            className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-md border border-input bg-background hover:bg-accent hover:text-accent-foreground shadow-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-foreground"
          >
            <Mic className="w-3.5 h-3.5 text-primary" />
            <span>Dictate Note</span>
          </button>
        )}

        {/* State: Requesting Microphone Permission */}
        {status === 'requesting' && (
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-md border border-border bg-muted/50 text-muted-foreground" aria-live="polite">
            <Loader2 className="w-3.5 h-3.5 animate-spin text-primary" />
            <span>Requesting microphone...</span>
          </div>
        )}

        {/* State: Recording */}
        {status === 'recording' && (
          <div className="inline-flex items-center gap-2 px-2.5 py-1 text-xs font-medium rounded-md border border-red-500/40 bg-red-500/10 text-red-700 dark:text-red-400 shadow-sm" aria-live="polite">
            <span className="w-2 h-2 rounded-full bg-red-600 animate-pulse" />
            <span>Listening</span>
            <span className="font-mono text-[11px] bg-red-500/20 px-1 py-0.2 rounded font-semibold">
              {formatTimer(recordingSeconds)}
            </span>

            <div className="flex items-center gap-1 ml-1 border-l border-red-500/30 pl-1.5">
              <button
                type="button"
                onClick={stopRecording}
                aria-label="Stop dictation and transcribe"
                title="Stop dictation and transcribe"
                className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-red-600 hover:bg-red-700 text-white text-[11px] font-medium shadow-xs transition-colors"
              >
                <Square className="w-2.5 h-2.5 fill-current" />
                <span>Stop</span>
              </button>
              <button
                type="button"
                onClick={cancelRecording}
                aria-label="Cancel dictation without modifying note"
                title="Cancel dictation (draft note is preserved unchanged)"
                className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded hover:bg-red-500/20 text-red-700 dark:text-red-300 text-[11px] transition-colors"
              >
                <X className="w-3 h-3" />
                <span>Cancel</span>
              </button>
            </div>
          </div>
        )}

        {/* State: Processing / Transcribing */}
        {status === 'processing' && (
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-md border border-primary/30 bg-primary/10 text-primary" aria-live="polite">
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
            <span>Transcribing note...</span>
          </div>
        )}

        {/* State: Success */}
        {status === 'success' && (
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-md border border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300" aria-live="polite">
            <Check className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
            <span>Transcript appended to draft</span>
          </div>
        )}

        {/* State: Error */}
        {status === 'error' && (
          <div className="flex items-center gap-1.5">
            <button
              type="button"
              onClick={startRecording}
              disabled={disabled}
              className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-md border border-input bg-background hover:bg-accent text-foreground shadow-sm transition-colors"
            >
              <Mic className="w-3.5 h-3.5 text-primary" />
              <span>Retry Dictation</span>
            </button>
          </div>
        )}
      </div>

      {/* Visible Error Banner if Error State */}
      {status === 'error' && errorMessage && (
        <div className="flex items-start gap-1.5 p-2 rounded-md bg-destructive/10 border border-destructive/20 text-destructive text-xs" role="alert">
          <AlertCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
          <div className="flex-1 leading-relaxed">{errorMessage}</div>
          <button
            type="button"
            onClick={() => {
              setErrorMessage('');
              setStatus('idle');
            }}
            className="text-muted-foreground hover:text-foreground text-xs p-0.5"
            aria-label="Dismiss error notice"
          >
            <X className="w-3 h-3" />
          </button>
        </div>
      )}
    </div>
  );
}
