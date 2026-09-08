import { api } from './client';

export const resourceRecruitmentApi = {
  getDashboard: () => api.get('/resource-recruitment/dashboard'),
  list: (params = {}) => api.get('/resource-recruitment', { params }),
  get: (id) => api.get(`/resource-recruitment/${id}`),
  create: (data) => api.post('/resource-recruitment', data),
  transition: (id, data) => api.post(`/resource-recruitment/${id}/transition`, data),
  update: (id, data) => api.patch(`/resource-recruitment/${id}`, data),
  endMember: (memberId) => api.post(`/resource-recruitment/members/${memberId}/end`),
};

export default resourceRecruitmentApi;
