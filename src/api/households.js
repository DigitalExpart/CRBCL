import { api } from './client';

export const householdsApi = {
  list: (params = {}) => api.entities.Household.list(params.sort, params.limit),
  get: (id) => api.entities.Household.get(id),
  create: (data) => api.entities.Household.create(data),
  addMember: (householdId, memberData) =>
    api.fetch(`/api/v1/households/${householdId}/members`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(memberData),
    }).then(res => res.json()),
};
