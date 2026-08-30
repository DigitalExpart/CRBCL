import { api } from './client';

export const providersApi = {
  list: (params = {}) => api.entities.Provider.list(params.sort, params.limit),
  get: (id) => api.entities.Provider.get(id),
  create: (data) => api.entities.Provider.create(data),
  update: (id, data) => api.entities.Provider.update(id, data),
};
