import { api } from './client';

export const plansApi = {
  listByCase: async (caseId, planType = null) => {
    const query = new URLSearchParams();
    if (planType) query.append('plan_type', planType);
    const qs = query.toString() ? `?${query.toString()}` : '';
    const res = await api.fetch(`/api/v1/cases/${caseId}/plans${qs}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to list plans');
    }
    return await res.json();
  },

  create: async (caseId, data) => {
    const res = await api.fetch(`/api/v1/cases/${caseId}/plans`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to create plan');
    }
    return await res.json();
  },

  getActiveGoals: async (caseId) => {
    const res = await api.fetch(`/api/v1/cases/${caseId}/active-goals`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to load active goals');
    }
    return await res.json();
  },

  get: async (planId) => {
    const res = await api.fetch(`/api/v1/plans/${planId}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to load plan');
    }
    return await res.json();
  },

  update: async (planId, data) => {
    const res = await api.fetch(`/api/v1/plans/${planId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to update plan');
    }
    return await res.json();
  },

  submit: async (planId, data = {}) => {
    const res = await api.fetch(`/api/v1/plans/${planId}/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to submit plan');
    }
    return await res.json();
  },

  approve: async (planId, data = {}) => {
    const res = await api.fetch(`/api/v1/plans/${planId}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to approve plan');
    }
    return await res.json();
  },

  returnForRevisions: async (planId, data) => {
    const res = await api.fetch(`/api/v1/plans/${planId}/return`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to return plan');
    }
    return await res.json();
  },

  finalize: async (planId, data = {}) => {
    const res = await api.fetch(`/api/v1/plans/${planId}/finalize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to finalize plan');
    }
    return await res.json();
  },

  lock: async (planId, data = {}) => {
    const res = await api.fetch(`/api/v1/plans/${planId}/lock`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to lock plan');
    }
    return await res.json();
  },

  unlock: async (planId, data) => {
    const res = await api.fetch(`/api/v1/plans/${planId}/unlock`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to unlock plan');
    }
    return await res.json();
  },

  createVersion: async (planId, data = {}) => {
    const res = await api.fetch(`/api/v1/plans/${planId}/versions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to create plan version');
    }
    return await res.json();
  },

  clone: async (planId, data) => {
    const res = await api.fetch(`/api/v1/plans/${planId}/clone`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to clone plan');
    }
    return await res.json();
  },

  addGoal: async (planId, data) => {
    const res = await api.fetch(`/api/v1/plans/${planId}/goals`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to add goal');
    }
    return await res.json();
  },

  updateGoal: async (goalId, data) => {
    const res = await api.fetch(`/api/v1/goals/${goalId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to update goal');
    }
    return await res.json();
  },

  completeGoal: async (goalId, data = {}) => {
    const res = await api.fetch(`/api/v1/goals/${goalId}/complete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to complete goal');
    }
    return await res.json();
  },

  addActivity: async (goalId, data) => {
    const res = await api.fetch(`/api/v1/goals/${goalId}/activities`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to add activity');
    }
    return await res.json();
  },

  completeActivity: async (activityId, data = {}) => {
    const res = await api.fetch(`/api/v1/activities/${activityId}/complete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to complete activity');
    }
    return await res.json();
  },

  addSignature: async (planId, data) => {
    const res = await api.fetch(`/api/v1/plans/${planId}/signatures`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to capture signature');
    }
    return await res.json();
  },

  addPhysicalSignature: async (planId, data) => {
    const res = await api.fetch(`/api/v1/plans/${planId}/physical-signature`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to upload physical signature');
    }
    return await res.json();
  },

  getPrintData: async (planId) => {
    const res = await api.fetch(`/api/v1/plans/${planId}/print`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to load printable plan');
    }
    return await res.json();
  },
};
