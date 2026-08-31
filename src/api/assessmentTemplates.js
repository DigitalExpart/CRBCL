import { api } from './client';

export const assessmentTemplatesApi = {
  list: async (params = {}) => {
    const query = new URLSearchParams();
    if (params.category) query.append('category', params.category);
    if (params.is_active !== undefined) query.append('is_active', params.is_active);
    const qs = query.toString() ? `?${query.toString()}` : '';
    const res = await api.fetch(`/api/v1/assessment-templates${qs}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || 'Failed to list assessment templates');
    }
    return await res.json();
  },

  get: async (identifier) => {
    const res = await api.fetch(`/api/v1/assessment-templates/${identifier}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || 'Failed to load assessment template');
    }
    return await res.json();
  },

  getVersion: async (versionId) => {
    const res = await api.fetch(`/api/v1/assessment-templates/versions/${versionId}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || 'Failed to load template version');
    }
    return await res.json();
  },

  create: async (data) => {
    const res = await api.fetch('/api/v1/assessment-templates', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || 'Failed to create template');
    }
    return await res.json();
  },

  createVersion: async (templateId, data) => {
    const res = await api.fetch(`/api/v1/assessment-templates/${templateId}/versions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || 'Failed to create template version');
    }
    return await res.json();
  },

  publishVersion: async (versionId) => {
    const res = await api.fetch(`/api/v1/assessment-templates/versions/${versionId}/publish`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || 'Failed to publish version');
    }
    return await res.json();
  },

  addSection: async (versionId, data) => {
    const res = await api.fetch(`/api/v1/assessment-templates/versions/${versionId}/sections`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || 'Failed to add section');
    }
    return await res.json();
  },

  addQuestion: async (sectionId, data) => {
    const res = await api.fetch(`/api/v1/assessment-templates/sections/${sectionId}/questions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || 'Failed to add question');
    }
    return await res.json();
  },
};
