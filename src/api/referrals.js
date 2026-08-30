import { api } from './client';

export const referralsApi = {
  list: (params = {}) => {
    const query = new URLSearchParams();
    if (params.page) query.append('page', params.page);
    if (params.page_size) query.append('page_size', params.page_size);
    if (params.search) query.append('search', params.search);
    if (params.status && params.status !== 'all') query.append('status', params.status);
    if (params.priority && params.priority !== 'all') query.append('priority', params.priority);
    if (params.concern_type) query.append('concern_type', params.concern_type);
    if (params.worker_id) query.append('worker_id', params.worker_id);
    if (params.team_id) query.append('team_id', params.team_id);
    if (params.date_from) query.append('date_from', params.date_from);
    if (params.date_to) query.append('date_to', params.date_to);

    const qs = query.toString();
    return api.fetch(`/api/v1/referrals${qs ? `?${qs}` : ''}`).then(res => res.json());
  },

  get: (id) =>
    api.fetch(`/api/v1/referrals/${id}`).then(res => res.json()),

  create: (data) =>
    api.fetch('/api/v1/referrals', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(res => res.json()),

  update: (id, data) =>
    api.fetch(`/api/v1/referrals/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(res => res.json()),

  // Involved People
  addPerson: (referralId, data) =>
    api.fetch(`/api/v1/referrals/${referralId}/people`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(res => res.json()),

  removePerson: (referralId, personId) =>
    api.fetch(`/api/v1/referrals/${referralId}/people/${personId}`, {
      method: 'DELETE',
    }),

  // Reporter
  getReporter: (referralId) =>
    api.fetch(`/api/v1/referrals/${referralId}/reporter`).then(res => res.json()),

  saveReporter: (referralId, data) =>
    api.fetch(`/api/v1/referrals/${referralId}/reporter`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(res => res.json()),

  // Incidents & Concerns
  addIncident: (referralId, data) =>
    api.fetch(`/api/v1/referrals/${referralId}/incidents`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(res => res.json()),

  addConcern: (referralId, data) =>
    api.fetch(`/api/v1/referrals/${referralId}/concerns`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(res => res.json()),

  deleteConcern: (referralId, concernId) =>
    api.fetch(`/api/v1/referrals/${referralId}/concerns/${concernId}`, {
      method: 'DELETE',
    }),

  // Prior History Discovery
  getPriorHistory: (referralId) =>
    api.fetch(`/api/v1/referrals/${referralId}/history`).then(res => res.json()),

  // Cross-Referral Links
  getLinks: (referralId) =>
    api.fetch(`/api/v1/referrals/${referralId}/links`).then(res => res.json()),

  createLink: (referralId, data) =>
    api.fetch(`/api/v1/referrals/${referralId}/links`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(res => res.json()),

  deleteLink: (referralId, linkId) =>
    api.fetch(`/api/v1/referrals/${referralId}/links/${linkId}`, {
      method: 'DELETE',
    }),

  // Decision & Dispositions
  saveDecision: (referralId, data) =>
    api.fetch(`/api/v1/referrals/${referralId}/decision`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(res => res.json()),

  submitForApproval: (referralId, data) =>
    api.fetch(`/api/v1/referrals/${referralId}/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(res => res.json()),

  approve: (referralId, data = {}) =>
    api.fetch(`/api/v1/referrals/${referralId}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(res => res.json()),

  returnToWorker: (referralId, returnReason) =>
    api.fetch(`/api/v1/referrals/${referralId}/return`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ return_reason: returnReason }),
    }).then(res => res.json()),

  getApprovalQueue: (params = {}) => {
    const query = new URLSearchParams();
    if (params.page) query.append('page', params.page);
    if (params.page_size) query.append('page_size', params.page_size);
    if (params.team_id) query.append('team_id', params.team_id);
    const qs = query.toString();
    return api.fetch(`/api/v1/referrals/approvals/queue${qs ? `?${qs}` : ''}`).then(res => res.json());
  },
};
