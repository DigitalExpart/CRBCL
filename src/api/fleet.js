import api from './client';

export const fleetApi = {
  // Fleet Dashboard Overview
  getFleetDashboard: () => api.get('/fleet/dashboard'),

  // Vehicles Directory & Lifecycle
  getVehicles: (params = {}) => api.get('/fleet/vehicles', { params }),
  createVehicle: (payload) => api.post('/fleet/vehicles', payload),
  getVehicleDetail: (id) => api.get(`/fleet/vehicles/${id}`),
  updateVehicle: (id, payload) => api.put(`/fleet/vehicles/${id}`, payload),
  archiveVehicle: (id) => api.delete(`/fleet/vehicles/${id}/archive`),

  // Check-Out / Check-In
  checkoutVehicle: (id, payload) => api.post(`/fleet/vehicles/${id}/checkout`, payload),
  checkinVehicle: (tripId, payload) => api.post(`/fleet/trips/${tripId}/checkin`, payload),

  // Maintenance & Insurance
  scheduleMaintenance: (payload) => api.post('/fleet/maintenance', payload),
  completeMaintenance: (id, payload) => api.put(`/fleet/maintenance/${id}/complete`, payload),
  createInsurance: (payload) => api.post('/fleet/insurance', payload),

  // Location Privacy & Capture
  recordLocation: (vehicleId, payload) => api.post(`/fleet/vehicles/${vehicleId}/location`, payload),
};
