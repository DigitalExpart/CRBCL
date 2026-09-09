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

  // Sprint 2: Inspections & Corrective Actions
  updateCorrectiveAction: (homeId, visitId, data) =>
    api.patch(`/placement-homes/${homeId}/visits/${visitId}/corrective-action`, data),

  // Sprint 2: Screenings & Clearances
  getClearances: (homeId) => api.get(`/placement-homes/${homeId}/clearances`),
  createClearance: (homeId, data) => api.post(`/placement-homes/${homeId}/clearances`, data),
  adjudicateBackgroundCheck: (checkId, data) =>
    api.post(`/background-checks/${checkId}/adjudicate`, data),

  // Sprint 2: Caregiver Assessments
  getAssessments: (homeId) => api.get(`/placement-homes/${homeId}/assessments`),
  createAssessment: (homeId, data) => api.post(`/placement-homes/${homeId}/assessments`, data),

  // Sprint 2: Training & Compliance
  getTrainings: (homeId) => api.get(`/placement-homes/${homeId}/training`),
  getTrainingCompliance: (homeId) => api.get(`/placement-homes/${homeId}/training/compliance`),
  createTraining: (homeId, data) => api.post(`/placement-homes/${homeId}/training`, data),
  verifyTraining: (trainingId, data) =>
    api.post(`/caregiver-trainings/${trainingId}/verify`, data),
};

export default placementHomesApi;
