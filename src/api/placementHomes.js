import { api } from './client';

export const placementHomesApi = {
  list: (params = {}) => api.get('/placement-homes', { params }),
  get: (id) => api.get(`/placement-homes/${id}`),
  create: (data) => api.post('/placement-homes', data),
  update: (id, data) => api.patch(`/placement-homes/${id}`, data),
  archive: (id) => api.post(`/placement-homes/${id}/archive`),
  getMetrics: () => api.get('/placement-homes/metrics'),
  getMapMarkers: () => api.get('/placement-homes/map'),
  
  // Household Members
  addMember: (homeId, data) => api.post(`/placement-homes/${homeId}/members`, data),
  updateMember: (homeId, memberId, data) => api.patch(`/placement-homes/${homeId}/members/${memberId}`, data),
  removeMember: (homeId, memberId) => api.delete(`/placement-homes/${homeId}/members/${memberId}`),
  
  // Licensing
  createLicense: (homeId, data) => api.post(`/placement-homes/${homeId}/licenses`, data),
  renewLicense: (homeId, data) => api.post(`/placement-homes/${homeId}/licenses/renew`, data),
  
  // Inspections & Visits
  createVisit: (homeId, data) => api.post(`/placement-homes/${homeId}/visits`, data),
  
  // Caregiver Contact Logs
  createContactLog: (homeId, data) => api.post(`/placement-homes/${homeId}/contact-logs`, data),
  
  // Background Screenings Summary
  getBackgroundChecks: (homeId) => api.get(`/placement-homes/${homeId}/background-checks`),
  
  // Longitudinal Placement History with redaction
  getPlacementHistory: (homeId) => api.get(`/placement-homes/${homeId}/placements`),
};

export default placementHomesApi;
