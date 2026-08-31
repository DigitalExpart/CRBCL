import { api } from './client';

export const casesApi = {
  // Core Case CRUD & Listing
  list: (params = {}) => api.entities.Case.list(params.sort, params.limit),
  filter: (query, sort, limit) => api.entities.Case.filter(query, sort, limit),
  get: (id) => api.entities.Case.get(id),
  create: (data) => api.entities.Case.create(data),
  update: (id, data) => api.entities.Case.update(id, data),
  delete: (id) => api.entities.Case.delete(id),

  // Snapshot & Lifecycle Commands
  getSnapshot: async (id) => {
    const res = await api.fetch(`/api/v1/cases/${id}/snapshot`);
    if (!res.ok) throw new Error('Failed to load case snapshot');
    return await res.json();
  },
  close: async (id, data) => {
    const res = await api.fetch(`/api/v1/cases/${id}/close`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || 'Failed to close case');
    }
    return await res.json();
  },
  reopen: async (id, data) => {
    const res = await api.fetch(`/api/v1/cases/${id}/reopen`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || 'Failed to reopen case');
    }
    return await res.json();
  },
  getStatusHistory: async (id) => {
    const res = await api.fetch(`/api/v1/cases/${id}/status-history`);
    if (!res.ok) throw new Error('Failed to load status history');
    return await res.json();
  },

  // People Roster
  getPeople: async (id) => {
    const res = await api.fetch(`/api/v1/cases/${id}/people`);
    if (!res.ok) throw new Error('Failed to load case roster');
    return await res.json();
  },
  addPerson: async (id, data) => {
    const res = await api.fetch(`/api/v1/cases/${id}/people`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || 'Failed to add person to case');
    }
    return await res.json();
  },
  removePerson: async (id, personLinkId) => {
    const res = await api.fetch(`/api/v1/cases/${id}/people/${personLinkId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to remove person from case');
    return true;
  },

  // Worker Assignments
  getAssignments: async (id) => {
    const res = await api.fetch(`/api/v1/cases/${id}/assignments`);
    if (!res.ok) throw new Error('Failed to load worker assignments');
    return await res.json();
  },
  assignWorker: async (id, data) => {
    const res = await api.fetch(`/api/v1/cases/${id}/assignments`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || 'Failed to assign worker');
    }
    return await res.json();
  },
  unassignWorker: async (id, assignmentId) => {
    const res = await api.fetch(`/api/v1/cases/${id}/assignments/${assignmentId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to end assignment');
    return true;
  },

  // External Workers
  getExternalWorkers: async (id) => {
    const res = await api.fetch(`/api/v1/cases/${id}/external-workers`);
    if (!res.ok) throw new Error('Failed to load external workers');
    return await res.json();
  },
  addExternalWorker: async (id, data) => {
    const res = await api.fetch(`/api/v1/cases/${id}/external-workers`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || 'Failed to add external worker');
    }
    return await res.json();
  },

  // Sources (Collateral & Other)
  getSources: async (id, category = null) => {
    const url = category ? `/api/v1/cases/${id}/sources?category=${category}` : `/api/v1/cases/${id}/sources`;
    const res = await api.fetch(url);
    if (!res.ok) throw new Error('Failed to load case sources');
    return await res.json();
  },
  addSource: async (id, data) => {
    const res = await api.fetch(`/api/v1/cases/${id}/sources`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || 'Failed to add case source');
    }
    return await res.json();
  },
  removeSource: async (id, sourceId) => {
    const res = await api.fetch(`/api/v1/cases/${id}/sources/${sourceId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to remove source');
    return true;
  },

  // Cross-Links
  getLinks: async (id) => {
    const res = await api.fetch(`/api/v1/cases/${id}/links`);
    if (!res.ok) throw new Error('Failed to load case links');
    return await res.json();
  },
  createLink: async (id, data) => {
    const res = await api.fetch(`/api/v1/cases/${id}/links`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || 'Failed to link cases');
    }
    return await res.json();
  },
  removeLink: async (id, linkId) => {
    const res = await api.fetch(`/api/v1/cases/${id}/links/${linkId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to remove link');
    return true;
  },

  // Case Restrictions (Conflict of Interest)
  getRestrictions: async (id) => {
    const res = await api.fetch(`/api/v1/cases/${id}/restrictions`);
    if (!res.ok) throw new Error('Failed to load case restrictions');
    return await res.json();
  },
  addRestriction: async (id, data) => {
    const res = await api.fetch(`/api/v1/cases/${id}/restrictions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || 'Failed to add restriction');
    }
    return await res.json();
  },
  removeRestriction: async (id, restrictionId, data) => {
    const res = await api.fetch(`/api/v1/cases/${id}/restrictions/${restrictionId}/remove`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || 'Failed to remove restriction');
    }
    return await res.json();
  },

  // Transfers & Supervisor Queue
  getTransfers: async (id) => {
    const res = await api.fetch(`/api/v1/cases/${id}/transfers`);
    if (!res.ok) throw new Error('Failed to load case transfers');
    return await res.json();
  },
  createTransfer: async (id, data) => {
    const res = await api.fetch(`/api/v1/cases/${id}/transfers`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || 'Failed to initiate transfer');
    }
    return await res.json();
  },
  getPendingTransfers: async () => {
    const res = await api.fetch(`/api/v1/transfers/pending`);
    if (!res.ok) throw new Error('Failed to load pending transfers');
    return await res.json();
  },
  submitTransfer: async (transferId) => {
    const res = await api.fetch(`/api/v1/transfers/${transferId}/submit`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to submit transfer');
    return await res.json();
  },
  approveTransfer: async (transferId, data) => {
    const res = await api.fetch(`/api/v1/transfers/${transferId}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || 'Failed to approve transfer');
    }
    return await res.json();
  },
  returnTransfer: async (transferId, data) => {
    const res = await api.fetch(`/api/v1/transfers/${transferId}/return`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || 'Failed to return transfer');
    }
    return await res.json();
  },
  denyTransfer: async (transferId, data) => {
    const res = await api.fetch(`/api/v1/transfers/${transferId}/deny`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || 'Failed to deny transfer');
    }
    return await res.json();
  },
};
