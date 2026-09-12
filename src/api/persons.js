import { api } from './client';

export const personsApi = {
  list: (params = {}) => {
    const query = new URLSearchParams();
    if (params.query) query.append('query', params.query);
    if (params.person_id_number) query.append('person_id_number', params.person_id_number);
    if (params.date_of_birth) query.append('date_of_birth', params.date_of_birth);
    if (params.limit) query.append('limit', params.limit);
    if (params.offset) query.append('offset', params.offset);
    const qs = query.toString();
    return api.fetch(`/api/v1/persons${qs ? `?${qs}` : ''}`).then(res => res.json());
  },

  getProfile: (personId) => api.fetch(`/api/v1/persons/${personId}`).then(res => res.json()),

  create: (data) =>
    api.fetch('/api/v1/persons', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(async res => {
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err?.detail?.error?.message || err?.detail?.message || 'Failed to create person');
      }
      return res.json();
    }),

  update: (personId, data) =>
    api.fetch(`/api/v1/persons/${personId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(async res => {
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err?.detail?.error?.message || err?.detail?.message || 'Failed to update person');
      }
      return res.json();
    }),

  checkDuplicates: (criteria) =>
    api.fetch('/api/v1/persons/duplicate-check', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(criteria),
    }).then(res => res.json()),

  uploadPhoto: (personId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.fetch(`/api/v1/persons/${personId}/photo`, {
      method: 'POST',
      body: formData,
    }).then(res => res.json());
  },
};
