import { api } from './client';

export const clientsApi = {
  list: (params = {}) => api.entities.Client.list(params.sort, params.limit),
  get: (id) => api.entities.Client.get(id),
  create: (data) => api.entities.Client.create(data),
  update: (id, data) => api.entities.Client.update(id, data),
  delete: (id) => api.entities.Client.delete(id),

  // Phase 2 Sub-Resources
  checkDuplicates: (criteria) =>
    api.fetch('/api/v1/clients/duplicate-check', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(criteria),
    }).then(res => res.json()),

  merge: (sourceId, targetId, reason, notes = '') =>
    api.fetch('/api/v1/clients/merge', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source_person_id: sourceId, target_person_id: targetId, reason, notes }),
    }).then(res => res.json()),

  getMedical: (clientId) =>
    api.fetch(`/api/v1/clients/${clientId}/medical`).then(res => res.json()),

  updateMedicalProfile: (clientId, data) =>
    api.fetch(`/api/v1/clients/${clientId}/medical`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(res => res.json()),

  addAllergy: (clientId, data) =>
    api.fetch(`/api/v1/clients/${clientId}/allergies`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(res => res.json()),

  addCondition: (clientId, data) =>
    api.fetch(`/api/v1/clients/${clientId}/conditions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(res => res.json()),

  addMedication: (clientId, data) =>
    api.fetch(`/api/v1/clients/${clientId}/medications`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(res => res.json()),

  getProviders: (clientId) =>
    api.fetch(`/api/v1/clients/${clientId}/providers`).then(res => res.json()),

  linkProvider: (clientId, data) =>
    api.fetch(`/api/v1/clients/${clientId}/providers`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(res => res.json()),

  getSchools: (clientId) =>
    api.fetch(`/api/v1/clients/${clientId}/schools`).then(res => res.json()),

  enrollSchool: (clientId, data) =>
    api.fetch(`/api/v1/clients/${clientId}/schools`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(res => res.json()),

  getTimeline: (clientId) =>
    api.fetch(`/api/v1/clients/${clientId}/timeline`).then(res => res.json()),
};
