import { api } from './client';

export const placementsApi = {
  // --- Active Efforts ---
  listActiveEfforts: async (caseId, params = {}) => {
    const query = new URLSearchParams(params);
    const qs = query.toString() ? `?${query.toString()}` : '';
    const res = await api.fetch(`/api/v1/cases/${caseId}/active-efforts${qs}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to list active efforts');
    }
    return await res.json();
  },

  createActiveEffort: async (caseId, data) => {
    const res = await api.fetch(`/api/v1/cases/${caseId}/active-efforts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to create active effort');
    }
    return await res.json();
  },

  updateActiveEffort: async (effortId, data) => {
    const res = await api.fetch(`/api/v1/active-efforts/${effortId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to update active effort');
    }
    return await res.json();
  },

  deleteActiveEffort: async (effortId) => {
    const res = await api.fetch(`/api/v1/active-efforts/${effortId}`, {
      method: 'DELETE',
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to delete active effort');
    }
    return await res.json();
  },

  // --- In-Home Placements ---
  listInHomePlacements: async (caseId, params = {}) => {
    const query = new URLSearchParams(params);
    const qs = query.toString() ? `?${query.toString()}` : '';
    const res = await api.fetch(`/api/v1/cases/${caseId}/in-home-placements${qs}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to list in-home placements');
    }
    return await res.json();
  },

  createInHomePlacement: async (caseId, data) => {
    const res = await api.fetch(`/api/v1/cases/${caseId}/in-home-placements`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to create in-home placement');
    }
    return await res.json();
  },

  updateInHomePlacement: async (placementId, data) => {
    const res = await api.fetch(`/api/v1/in-home-placements/${placementId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to update in-home placement');
    }
    return await res.json();
  },

  // --- Removal Episodes ---
  listRemovals: async (caseId, params = {}) => {
    const query = new URLSearchParams(params);
    const qs = query.toString() ? `?${query.toString()}` : '';
    const res = await api.fetch(`/api/v1/cases/${caseId}/removals${qs}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to list removal episodes');
    }
    return await res.json();
  },

  createRemoval: async (caseId, data) => {
    const res = await api.fetch(`/api/v1/cases/${caseId}/removals`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to create removal episode');
    }
    return await res.json();
  },

  getRemoval: async (removalId) => {
    const res = await api.fetch(`/api/v1/removals/${removalId}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to load removal episode');
    }
    return await res.json();
  },

  updateRemoval: async (removalId, data) => {
    const res = await api.fetch(`/api/v1/removals/${removalId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to update removal episode');
    }
    return await res.json();
  },

  // --- Placement Episodes ---
  listPlacements: async (caseId, params = {}) => {
    const query = new URLSearchParams(params);
    const qs = query.toString() ? `?${query.toString()}` : '';
    const res = await api.fetch(`/api/v1/cases/${caseId}/placements${qs}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to list placement episodes');
    }
    return await res.json();
  },

  createPlacement: async (caseId, data) => {
    const res = await api.fetch(`/api/v1/cases/${caseId}/placements`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to create placement episode');
    }
    return await res.json();
  },

  getPlacement: async (placementId) => {
    const res = await api.fetch(`/api/v1/placements/${placementId}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to load placement episode');
    }
    return await res.json();
  },

  updatePlacement: async (placementId, data) => {
    const res = await api.fetch(`/api/v1/placements/${placementId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to update placement episode');
    }
    return await res.json();
  },

  getActivePlacementForChild: async (childId) => {
    const res = await api.fetch(`/api/v1/clients/${childId}/active-placement`);
    if (res.status === 404) return null;
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to check active placement');
    }
    return await res.json();
  },

  getClientPlacementHistory: async (childId) => {
    const res = await api.fetch(`/api/v1/clients/${childId}/placement-episodes`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to load placement history');
    }
    return await res.json();
  },

  // --- Respite Care ---
  listRespite: async (placementId) => {
    const res = await api.fetch(`/api/v1/placements/${placementId}/respite`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to list respite care');
    }
    return await res.json();
  },

  createRespite: async (placementId, data) => {
    const res = await api.fetch(`/api/v1/placements/${placementId}/respite`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to schedule respite');
    }
    return await res.json();
  },

  updateRespite: async (respiteId, data) => {
    const res = await api.fetch(`/api/v1/respite/${respiteId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to update respite');
    }
    return await res.json();
  },

  // --- Discharge ---
  listDischarges: async (caseId, params = {}) => {
    const query = new URLSearchParams(params);
    const qs = query.toString() ? `?${query.toString()}` : '';
    const res = await api.fetch(`/api/v1/cases/${caseId}/discharges${qs}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to list discharges');
    }
    return await res.json();
  },

  createDischarge: async (caseId, data) => {
    const res = await api.fetch(`/api/v1/cases/${caseId}/discharges`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to discharge placement');
    }
    return await res.json();
  },

  updateDischarge: async (dischargeId, data) => {
    const res = await api.fetch(`/api/v1/discharges/${dischargeId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to update discharge');
    }
    return await res.json();
  },

  // --- Permanency Plans ---
  listPermanencyPlans: async (caseId, params = {}) => {
    const query = new URLSearchParams(params);
    const qs = query.toString() ? `?${query.toString()}` : '';
    const res = await api.fetch(`/api/v1/cases/${caseId}/permanency-plans${qs}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to list permanency plans');
    }
    return await res.json();
  },

  createPermanencyPlan: async (caseId, data) => {
    const res = await api.fetch(`/api/v1/cases/${caseId}/permanency-plans`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to create permanency plan');
    }
    return await res.json();
  },

  getPermanencyPlan: async (planId) => {
    const res = await api.fetch(`/api/v1/permanency-plans/${planId}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to load permanency plan');
    }
    return await res.json();
  },

  updatePermanencyPlan: async (planId, data) => {
    const res = await api.fetch(`/api/v1/permanency-plans/${planId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to update permanency plan');
    }
    return await res.json();
  },

  // --- Family Visitation Plans ---
  listVisitationPlans: async (caseId, params = {}) => {
    const query = new URLSearchParams(params);
    const qs = query.toString() ? `?${query.toString()}` : '';
    const res = await api.fetch(`/api/v1/cases/${caseId}/visitation-plans${qs}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to list visitation plans');
    }
    return await res.json();
  },

  createVisitationPlan: async (caseId, data) => {
    const res = await api.fetch(`/api/v1/cases/${caseId}/visitation-plans`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to create visitation plan');
    }
    return await res.json();
  },

  getVisitationPlan: async (planId) => {
    const res = await api.fetch(`/api/v1/visitation-plans/${planId}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to load visitation plan');
    }
    return await res.json();
  },

  updateVisitationPlan: async (planId, data) => {
    const res = await api.fetch(`/api/v1/visitation-plans/${planId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to update visitation plan');
    }
    return await res.json();
  },

  // --- Court Events ---
  listCourtEvents: async (caseId, params = {}) => {
    const query = new URLSearchParams(params);
    const qs = query.toString() ? `?${query.toString()}` : '';
    const res = await api.fetch(`/api/v1/cases/${caseId}/court-events${qs}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to list court events');
    }
    return await res.json();
  },

  createCourtEvent: async (caseId, data) => {
    const res = await api.fetch(`/api/v1/cases/${caseId}/court-events`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to create court event');
    }
    return await res.json();
  },

  getCourtEvent: async (eventId) => {
    const res = await api.fetch(`/api/v1/court-events/${eventId}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to load court event');
    }
    return await res.json();
  },

  updateCourtEvent: async (eventId, data) => {
    const res = await api.fetch(`/api/v1/court-events/${eventId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to update court event');
    }
    return await res.json();
  },

  // --- Background Checks ---
  listBackgroundChecks: async (params = {}) => {
    const query = new URLSearchParams(params);
    const qs = query.toString() ? `?${query.toString()}` : '';
    const res = await api.fetch(`/api/v1/background-checks${qs}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to list background checks');
    }
    return await res.json();
  },

  createBackgroundCheck: async (data) => {
    const res = await api.fetch(`/api/v1/background-checks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to submit background check');
    }
    return await res.json();
  },

  getBackgroundCheck: async (checkId) => {
    const res = await api.fetch(`/api/v1/background-checks/${checkId}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to load background check');
    }
    return await res.json();
  },

  updateBackgroundCheck: async (checkId, data) => {
    const res = await api.fetch(`/api/v1/background-checks/${checkId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to update background check');
    }
    return await res.json();
  },

  adjudicateBackgroundCheck: async (checkId, data) => {
    const res = await api.fetch(`/api/v1/background-checks/${checkId}/adjudicate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || err?.detail || 'Failed to adjudicate background check');
    }
    return await res.json();
  },
};
