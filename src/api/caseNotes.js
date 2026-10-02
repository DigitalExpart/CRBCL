import { api } from './client';

export const caseNotesApi = {
  // List Notes with filtering, pagination, search, contact types, and date ranges
  listForCase: async (caseId, params = {}) => {
    const query = new URLSearchParams();
    if (params.contact_type && params.contact_type !== 'all') query.set('contact_type', params.contact_type);
    if (params.location && params.location !== 'all') query.set('location', params.location);
    if (params.status && params.status !== 'all') query.set('status', params.status);
    if (params.appointment_status && params.appointment_status !== 'all') query.set('appointment_status', params.appointment_status);
    if (params.search) query.set('search', params.search);
    if (params.author_name) query.set('author_name', params.author_name);
    if (params.start_date) query.set('start_date', params.start_date);
    if (params.end_date) query.set('end_date', params.end_date);
    if (params.include_confidential !== undefined) query.set('include_confidential', String(params.include_confidential));
    if (params.offset !== undefined) query.set('offset', String(params.offset));
    if (params.limit !== undefined) query.set('limit', String(params.limit));
    if (params.sort_order) query.set('sort_order', params.sort_order);

    const queryString = query.toString();
    const url = `/api/v1/cases/${caseId}/notes${queryString ? '?' + queryString : ''}`;
    const res = await api.fetch(url);
    if (!res.ok) throw new Error('Failed to load case notes');
    return await res.json();
  },

  // Note CRUD
  get: async (id) => {
    const res = await api.fetch(`/api/v1/case-notes/${id}`);
    if (!res.ok) throw new Error('Failed to load case note');
    return await res.json();
  },
  create: async (caseId, data) => {
    const res = await api.fetch(`/api/v1/cases/${caseId}/notes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || 'Failed to create case note');
    }
    return await res.json();
  },
  update: async (id, data) => {
    const res = await api.fetch(`/api/v1/case-notes/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || 'Failed to update case note');
    }
    return await res.json();
  },
  complete: async (id) => {
    const res = await api.fetch(`/api/v1/case-notes/${id}/complete`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to complete note');
    return await res.json();
  },
  lock: async (id) => {
    const res = await api.fetch(`/api/v1/case-notes/${id}/lock`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to lock note');
    return await res.json();
  },
  addAddendum: async (id, data) => {
    const res = await api.fetch(`/api/v1/case-notes/${id}/addenda`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || 'Failed to add addendum');
    }
    return await res.json();
  },
  clone: async (id) => {
    const res = await api.fetch(`/api/v1/case-notes/${id}/clone`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to clone note');
    return await res.json();
  },

  // Service Metrics & Reporting
  getMetrics: async (caseId) => {
    const res = await api.fetch(`/api/v1/cases/${caseId}/notes/metrics`);
    if (!res.ok) throw new Error('Failed to load note metrics');
    return await res.json();
  },
  exportCsvUrl: (caseId) => `/api/v1/cases/${caseId}/notes/export`,

  // Speech-to-Text Transcription for Drafting
  getTranscriptionStatus: async (caseId) => {
    const res = await api.fetch(`/api/v1/cases/${caseId}/notes/transcribe/status`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail?.error?.message || 'Failed to check speech service status');
    }
    return await res.json();
  },

  transcribeAudio: async (caseId, audioBlob, language = 'en') => {
    const formData = new FormData();
    formData.append('file', audioBlob, 'recording.webm');
    formData.append('language', language);

    const res = await api.fetch(`/api/v1/cases/${caseId}/notes/transcribe`, {
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
};
