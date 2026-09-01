import apiClient from './client';

export const calendarApi = {
  getPersonalSchedule: async (startAt, endAt, eventTypes = []) => {
    const params = new URLSearchParams();
    if (startAt) params.append('start_at', typeof startAt === 'string' ? startAt : startAt.toISOString());
    if (endAt) params.append('end_at', typeof endAt === 'string' ? endAt : endAt.toISOString());
    if (eventTypes && eventTypes.length > 0) {
      eventTypes.forEach(t => params.append('event_types', t));
    }
    const response = await apiClient.get(`/calendar/my-schedule?${params.toString()}`);
    return response.data;
  },

  getTeamSchedule: async (startAt, endAt, teamId = null, workerIds = [], eventTypes = []) => {
    const params = new URLSearchParams();
    if (startAt) params.append('start_at', typeof startAt === 'string' ? startAt : startAt.toISOString());
    if (endAt) params.append('end_at', typeof endAt === 'string' ? endAt : endAt.toISOString());
    if (teamId) params.append('team_id', teamId);
    if (workerIds && workerIds.length > 0) {
      workerIds.forEach(w => params.append('worker_ids', w));
    }
    if (eventTypes && eventTypes.length > 0) {
      eventTypes.forEach(t => params.append('event_types', t));
    }
    const response = await apiClient.get(`/calendar/team-schedule?${params.toString()}`);
    return response.data;
  },

  getEvent: async (id) => {
    const response = await apiClient.get(`/calendar/events/${id}`);
    return response.data;
  },

  createEvent: async (payload) => {
    const response = await apiClient.post('/calendar/events', payload);
    return response.data;
  },

  updateEvent: async (id, payload) => {
    const response = await apiClient.patch(`/calendar/events/${id}`, payload);
    return response.data;
  },

  deleteEvent: async (id) => {
    const response = await apiClient.delete(`/calendar/events/${id}`);
    return response.data;
  },
};

export default calendarApi;
