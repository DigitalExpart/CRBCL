import apiClient from './client';

export const staffingApi = {
  listSessions: async (params = {}) => {
    const query = new URLSearchParams();
    if (params.status) query.append('status', params.status);
    if (params.team_id) query.append('team_id', params.team_id);
    if (params.facilitator_id) query.append('facilitator_id', params.facilitator_id);
    if (params.from_date) query.append('from_date', params.from_date);
    if (params.to_date) query.append('to_date', params.to_date);
    if (params.page) query.append('page', params.page);
    if (params.page_size) query.append('page_size', params.page_size);
    const response = await apiClient.get(`/staffing/sessions?${query.toString()}`);
    return response.data;
  },

  getSession: async (id) => {
    const response = await apiClient.get(`/staffing/sessions/${id}`);
    return response.data;
  },

  createSession: async (payload) => {
    const response = await apiClient.post('/staffing/sessions', payload);
    return response.data;
  },

  updateSession: async (id, payload) => {
    const response = await apiClient.patch(`/staffing/sessions/${id}`, payload);
    return response.data;
  },

  addAttendee: async (sessionId, payload) => {
    const response = await apiClient.post(`/staffing/sessions/${sessionId}/attendees`, payload);
    return response.data;
  },

  addCase: async (sessionId, payload) => {
    const response = await apiClient.post(`/staffing/sessions/${sessionId}/cases`, payload);
    return response.data;
  },

  updateCaseReview: async (sessionId, caseId, payload) => {
    const response = await apiClient.patch(`/staffing/sessions/${sessionId}/cases/${caseId}`, payload);
    return response.data;
  },

  completeSession: async (sessionId, minutes = null) => {
    const response = await apiClient.post(`/staffing/sessions/${sessionId}/complete`, { minutes });
    return response.data;
  },

  getCaseBuckets: async (teamId = null) => {
    const query = teamId ? `?team_id=${teamId}` : '';
    const response = await apiClient.get(`/staffing/case-buckets${query}`);
    return response.data;
  },
};

export default staffingApi;
