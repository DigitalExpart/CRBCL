import { api } from './client';

export const assessmentsApi = {
  listByCase: async (caseId, params = {}) => {
    const query = new URLSearchParams();
    if (params.template_key) query.append('template_key', params.template_key);
    if (params.status) query.append('status', params.status);
    if (params.limit) query.append('limit', params.limit);
    if (params.offset) query.append('offset', params.offset);
    const qs = query.toString() ? `?${query.toString()}` : '';
    const res = await api.fetch(`/api/v1/cases/${caseId}/assessments${qs}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || 'Failed to list case assessments');
    }
    return await res.json();
  },

  create: async (caseId, data) => {
    const res = await api.fetch(`/api/v1/cases/${caseId}/assessments`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || 'Failed to create assessment');
    }
    return await res.json();
  },

  get: async (assessmentId) => {
    const res = await api.fetch(`/api/v1/assessments/${assessmentId}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || 'Failed to load assessment');
    }
    return await res.json();
  },

  saveAnswers: async (assessmentId, data) => {
    const res = await api.fetch(`/api/v1/assessments/${assessmentId}/answers`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || 'Failed to save answers');
    }
    return await res.json();
  },

  complete: async (assessmentId, data) => {
    const res = await api.fetch(`/api/v1/assessments/${assessmentId}/complete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || 'Failed to complete assessment');
    }
    return await res.json();
  },

  lock: async (assessmentId, data = {}) => {
    const res = await api.fetch(`/api/v1/assessments/${assessmentId}/lock`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || 'Failed to lock assessment');
    }
    return await res.json();
  },

  unlock: async (assessmentId, data) => {
    const res = await api.fetch(`/api/v1/assessments/${assessmentId}/unlock`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || 'Failed to unlock assessment');
    }
    return await res.json();
  },

  reassign: async (assessmentId, data) => {
    const res = await api.fetch(`/api/v1/assessments/${assessmentId}/reassign`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || 'Failed to reassign assessment');
    }
    return await res.json();
  },

  compare: async (assessmentId, previousId) => {
    const res = await api.fetch(`/api/v1/assessments/${assessmentId}/compare/${previousId}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || 'Failed to compare assessments');
    }
    return await res.json();
  },
};
