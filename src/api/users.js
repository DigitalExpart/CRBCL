import { api } from './client';

export const usersApi = {
  list: (params = {}) => api.entities.User.list(params.sort, params.limit),
  get: (id) => api.entities.User.get(id),
  create: (data) => api.entities.User.create(data),
  update: (id, data) => api.entities.User.update(id, data),
};
