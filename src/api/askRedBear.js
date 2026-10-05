import { api } from './client';

/**
 * Ask Red Bear AI & Speech API Client
 *
 * Provides typed methods for Ask Red Bear queries, speech transcription, and administrative audits.
 */
export const askRedBearApi = {
  /**
   * Submit an authorized prompt to Ask Red Bear assistive AI.
   */
  query: async (prompt, caseId = null) => {
    const payload = { prompt };
    if (caseId) payload.case_id = caseId;
    const res = await api.fetch('/api/v1/ask-red-bear/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail?.error?.message || err?.detail || 'Failed to query Ask Red Bear');
    }
    return await res.json();
  },

  /**
   * Fetch readiness and availability status of local speech transcription for Ask Red Bear.
   */
  getTranscriptionStatus: async () => {
    const res = await api.fetch('/api/v1/ask-red-bear/transcribe/status');
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail?.error?.message || 'Failed to check speech service status');
    }
    return await res.json();
  },

  /**
   * Upload transient in-memory audio recording for Ask Red Bear prompt transcription.
   * Does NOT submit the prompt to Ask Red Bear.
   */
  transcribeAudio: async (audioBlob, language = 'en', options = {}) => {
    const formData = new FormData();
    formData.append('file', audioBlob, 'prompt.webm');
    formData.append('language', language);
    if (options.caseId) {
      formData.append('case_id', options.caseId);
    }

    const res = await api.fetch('/api/v1/ask-red-bear/transcribe', {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      const msg =
        err?.error?.message ||
        err?.detail?.error?.message ||
        (res.status === 503
          ? 'Speech-to-text is unavailable until an approved transcription provider is configured.'
          : 'Transcription failed');
      const errorObj = new Error(msg);
      errorObj.status = res.status;
      errorObj.code = err?.error?.code || err?.detail?.error?.code;
      throw errorObj;
    }
    return await res.json();
  },

  /**
   * Fetch audit records of Ask Red Bear AI requests (requires admin permissions).
   */
  getAudits: async () => {
    const res = await api.fetch('/api/v1/ask-red-bear/audits');
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail?.error?.message || 'Failed to fetch AI audits');
    }
    return await res.json();
  },
};
