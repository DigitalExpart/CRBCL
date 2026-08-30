import { api } from './client';

export const schoolsApi = {
  list: (params = {}) => api.entities.School.list(params.sort, params.limit),
  get: (id) => api.entities.School.get(id),
  create: (data) => api.entities.School.create(data),
};
