import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Square, Check, X, Volume2 } from 'lucide-react';

export function TalkToTextControl({ onTranscriptReady, buttonText = "Talk-to-Text", disabled = false }) {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [isSupported, setIsSupported] = useState(true);
  const recognitionRef = useRef(null);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setIsSupported(false);
    }
  }, []);

  const startListening = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Voice transcription is not supported in this browser. Please type directly into the note editor.");
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-CA';

      let finalTranscript = "";

      recognition.onresult = (event) => {
        let currentText = "";
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const text = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += text + " ";
          } else {
            currentText += text;
          }
        }
        setTranscript((finalTranscript + currentText).trim());
      };

      recognition.onerror = (event) => {
        console.error("Speech recognition error:", event.error);
        setIsRecording(false);
      };

      recognition.onend = () => {
        setIsRecording(false);
      };

      recognitionRef.current = recognition;
      recognition.start();
      setIsRecording(true);
      setTranscript("");
      setShowReviewModal(true);
    } catch (err) {
      console.error("Failed to start speech recognition:", err);
    }
  };

  const stopListening = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    setIsRecording(false);
  };

  const handleApply = () => {
    if (transcript.trim() && onTranscriptReady) {
      onTranscriptReady(transcript.trim());
    }
    setShowReviewModal(false);
    setTranscript("");
  };

  const handleCancel = () => {
    stopListening();
    setShowReviewModal(false);
    setTranscript("");
  };

  return (
    <>
      <button
        type="button"
        onClick={startListening}
        disabled={disabled || !isSupported}
        className={`inline-flex items-center px-3 py-1.5 border text-xs font-semibold rounded-md shadow-sm transition-colors ${
          isRecording
            ? 'border-red-500 text-red-700 bg-red-50 animate-pulse'
            : 'border-slate-300 text-slate-700 bg-white hover:bg-slate-50'
        } disabled:opacity-50 disabled:cursor-not-allowed`}
        title={isSupported ? "Click to dictate text using speech recognition" : "Speech recognition unsupported in this browser"}
      >
        <Mic className={`h-4 w-4 mr-1.5 ${isRecording ? 'text-red-600 animate-bounce' : 'text-slate-500'}`} />
        {isRecording ? "Recording..." : buttonText}
      </button>

      {showReviewModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-lg w-full p-6 space-y-4 border border-slate-200">
            <div className="flex items-center justify-between border-b pb-3">
              <div className="flex items-center space-x-2">
                <Volume2 className="h-5 w-5 text-indigo-600" />
                <h3 className="text-base font-bold text-slate-900">Talk-to-Text Dictation Review</h3>
              </div>
              <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${isRecording ? 'bg-red-100 text-red-800' : 'bg-slate-100 text-slate-800'}`}>
                {isRecording ? "Listening..." : "Stopped"}
              </span>
            </div>

            <div className="space-y-2">
              <p className="text-xs text-slate-500">
                Dictated transcript preview (Drafting assistance — review carefully before inserting into note):
              </p>
              <textarea
                value={transcript}
                onChange={(e) => setTranscript(e.target.value)}
                placeholder="Speak clearly into your microphone..."
                rows={5}
                className="w-full rounded-md border-slate-300 shadow-sm text-sm p-3 focus:ring-indigo-500 focus:border-indigo-500 border"
              />
            </div>

            <div className="flex items-center justify-between pt-2">
              {isRecording ? (
                <button
                  type="button"
                  onClick={stopListening}
                  className="inline-flex items-center px-3 py-1.5 border border-red-300 text-xs font-medium rounded text-red-700 bg-red-50 hover:bg-red-100"
                >
                  <Square className="h-3.5 w-3.5 mr-1 fill-current" />
                  Stop Recording
                </button>
              ) : (
                <button
                  type="button"
                  onClick={startListening}
                  className="inline-flex items-center px-3 py-1.5 border border-slate-300 text-xs font-medium rounded text-slate-700 bg-slate-50 hover:bg-slate-100"
                >
                  <Mic className="h-3.5 w-3.5 mr-1 text-slate-500" />
                  Resume Dictation
                </button>
              )}

              <div className="flex space-x-2">
                <button
                  type="button"
                  onClick={handleCancel}
                  className="inline-flex items-center px-3 py-1.5 border border-slate-300 text-xs font-medium rounded text-slate-700 bg-white hover:bg-slate-50"
                >
                  <X className="h-3.5 w-3.5 mr-1" />
                  Discard
                </button>
                <button
                  type="button"
                  onClick={handleApply}
                  disabled={!transcript.trim()}
                  className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50"
                >
                  <Check className="h-3.5 w-3.5 mr-1" />
                  Insert Into Note
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
