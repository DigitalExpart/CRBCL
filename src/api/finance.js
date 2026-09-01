/**
 * CRBCL Finance & Placement Billing API Client (Phase 10)
 * All endpoints match the backend /api/v1/finance router exactly.
 */

import apiClient from './client';

export const financeApi = {
  // ── Metrics & Dashboard ──
  getDashboardMetrics: async () => {
    const res = await apiClient.get('/finance/dashboard-metrics');
    return res.data;
  },

  // ── Funding Sources ──
  getFundingSources: async (status = null) => {
    const params = status ? { status } : {};
    const res = await apiClient.get('/finance/funding-sources', { params });
    return res.data;
  },

  createFundingSource: async (data) => {
    const res = await apiClient.post('/finance/funding-sources', data);
    return res.data;
  },

  // ── Budget Lines ──
  getBudgetLines: async (fiscalYear = null, isActive = null) => {
    const params = {};
    if (fiscalYear) params.fiscal_year = fiscalYear;
    if (isActive !== null) params.is_active = isActive;
    const res = await apiClient.get('/finance/budget-lines', { params });
    return res.data;
  },

  createBudgetLine: async (data) => {
    const res = await apiClient.post('/finance/budget-lines', data);
    return res.data;
  },

  // ── Service Requests (Purchase Orders & Reimbursements) ──
  getServiceRequests: async (params = {}) => {
    const res = await apiClient.get('/finance/requests', { params });
    return res.data;
  },

  getServiceRequestById: async (id) => {
    const res = await apiClient.get(`/finance/requests/${id}`);
    return res.data;
  },

  createServiceRequest: async (data) => {
    const res = await apiClient.post('/finance/requests', data);
    return res.data;
  },

  updateServiceRequest: async (id, data) => {
    const res = await apiClient.put(`/finance/requests/${id}`, data);
    return res.data;
  },

  submitServiceRequest: async (id) => {
    const res = await apiClient.post(`/finance/requests/${id}/submit`);
    return res.data;
  },

  approveServiceRequest: async (id, comments = '') => {
    const res = await apiClient.post(`/finance/requests/${id}/approve`, { comments });
    return res.data;
  },

  returnServiceRequest: async (id, reason) => {
    const res = await apiClient.post(`/finance/requests/${id}/return`, { reason });
    return res.data;
  },

  denyServiceRequest: async (id, reason) => {
    const res = await apiClient.post(`/finance/requests/${id}/deny`, { reason });
    return res.data;
  },

  // ── Billing Rates ──
  getBillingRates: async (homeType = null, activeOnly = true) => {
    const params = { active_only: activeOnly };
    if (homeType) params.home_type = homeType;
    const res = await apiClient.get('/finance/rates', { params });
    return res.data;
  },

  createBillingRate: async (data) => {
    const res = await apiClient.post('/finance/rates', data);
    return res.data;
  },

  // ── Invoices & Placement Billing ──
  getInvoices: async (params = {}) => {
    const res = await apiClient.get('/finance/invoices', { params });
    return res.data;
  },

  getInvoiceById: async (id) => {
    const res = await apiClient.get(`/finance/invoices/${id}`);
    return res.data;
  },

  generateDraftInvoice: async (data) => {
    const res = await apiClient.post('/finance/invoices/generate', data);
    return res.data;
  },

  finalizeInvoice: async (id) => {
    const res = await apiClient.post(`/finance/invoices/${id}/finalize`);
    return res.data;
  },

  voidInvoice: async (id, voidReason) => {
    const res = await apiClient.post(`/finance/invoices/${id}/void`, { void_reason: voidReason });
    return res.data;
  },

  // ── Financial Ledger ──
  /**
   * Fetches the unified financial ledger (service requests + invoices).
   * Backend returns { items: [...], total: N }
   */
  getLedger: async (params = {}) => {
    const res = await apiClient.get('/finance/ledger', { params });
    return res.data;
  },

  /**
   * Downloads ledger as XLSX. Returns a Blob for client-side file save.
   */
  exportLedger: async (params = {}) => {
    const res = await apiClient.get('/finance/ledger/export', {
      params,
      responseType: 'blob',
    });
    return res.data;
  },

  // ── Spending Overview ──
  getCaseSpending: async (caseId) => {
    const res = await apiClient.get(`/finance/spending/cases/${caseId}`);
    return res.data;
  },

  getFamilySpending: async (familyId) => {
    const res = await apiClient.get(`/finance/spending/families/${familyId}`);
    return res.data;
  },
};

export default financeApi;
