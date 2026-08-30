import { api } from './client';

export const familiesApi = {
  list: (params = {}) => api.entities.Family.list(params.sort, params.limit),
  get: (id) => api.entities.Family.get(id),
  create: (data) => api.entities.Family.create(data),
  update: (id, data) => api.entities.Family.update(id, data),
  delete: (id) => api.entities.Family.delete(id),

  // Phase 2 Sub-Resources
  getMembers: (familyId) =>
    api.fetch(`/api/v1/families/${familyId}/members`).then(res => res.json()),

  addMember: (familyId, data) =>
    api.fetch(`/api/v1/families/${familyId}/members`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(res => res.json()),

  getRelationships: (familyId) =>
    api.fetch(`/api/v1/families/${familyId}/relationships`).then(res => res.json()),

  addRelationship: (familyId, data) =>
    api.fetch(`/api/v1/families/${familyId}/relationships`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(res => res.json()),

  getGenogram: (familyId) =>
    api.fetch(`/api/v1/families/${familyId}/genogram`).then(res => res.json()),

  getMap: (familyId) =>
    api.fetch(`/api/v1/families/${familyId}/map`).then(res => res.json()),
};
