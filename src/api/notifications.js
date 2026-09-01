import apiClient from './client';

export const notificationsApi = {
  listNotifications: async (params = {}) => {
    const query = new URLSearchParams();
    if (params.is_read !== undefined && params.is_read !== null) query.append('is_read', params.is_read);
    if (params.type) query.append('type', params.type);
    if (params.page) query.append('page', params.page);
    if (params.page_size) query.append('page_size', params.page_size);
    const response = await apiClient.get(`/notifications?${query.toString()}`);
    return response.data;
  },

  getUnreadCount: async () => {
    const response = await apiClient.get('/notifications/unread-count');
    return response.data;
  },

  markAsRead: async (id) => {
    const response = await apiClient.post(`/notifications/${id}/read`);
    return response.data;
  },

  markAllAsRead: async () => {
    const response = await apiClient.post('/notifications/read-all');
    return response.data;
  },

  getPreferences: async () => {
    const response = await apiClient.get('/notification-preferences');
    return response.data;
  },

  updatePreference: async (payload) => {
    const response = await apiClient.patch('/notification-preferences', payload);
    return response.data;
  },

  listDeliveries: async (params = {}) => {
    const query = new URLSearchParams();
    if (params.status) query.append('status', params.status);
    if (params.channel) query.append('channel', params.channel);
    if (params.page) query.append('page', params.page);
    if (params.page_size) query.append('page_size', params.page_size);
    const response = await apiClient.get(`/notifications/deliveries?${query.toString()}`);
    return response.data;
  },

  retryDelivery: async (id) => {
    const response = await apiClient.post(`/notifications/deliveries/${id}/retry`);
    return response.data;
  },
};

export default notificationsApi;
