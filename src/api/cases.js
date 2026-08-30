import { api } from './client';

export const casesApi = {
  list: (params = {}) => api.entities.Case.list(params.sort, params.limit),
  filter: (query, sort, limit) => api.entities.Case.filter(query, sort, limit),
  get: (id) => api.entities.Case.get(id),
  create: (data) => api.entities.Case.create(data),
  update: (id, data) => api.entities.Case.update(id, data),
  delete: (id) => api.entities.Case.delete(id),
};
