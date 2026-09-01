import api from './client';

export const reportingApi = {
  // Catalogue & Canned Reports
  getCatalogue: () => api.get('/reports/catalogue'),
  getCannedIntakeMonthly: (startDate, endDate) =>
    api.get(`/reports/canned/intake-monthly?start_date=${startDate}&end_date=${endDate}`),
  getCannedActiveCasesWorker: () => api.get('/reports/canned/active-cases-worker'),
  getCannedCasesTypeStatus: () => api.get('/reports/canned/cases-type-status'),
  getCannedChildrenPlacement: () => api.get('/reports/canned/children-placement'),
  getCannedFinancialSummary: () => api.get('/reports/canned/financial-summary'),

  // Ad-Hoc Report Engine
  runAdhocReport: (payload) => api.post('/reports/adhoc', payload),

  // Saved Reports & Runs
  getSavedReports: () => api.get('/reports/saved'),
  createSavedReport: (payload) => api.post('/reports/saved', payload),
  runSavedReport: (reportId) => api.post(`/reports/saved/${reportId}/run`),
  deleteSavedReport: (reportId) => api.delete(`/reports/saved/${reportId}`),

  // Exports
  exportReport: (payload) =>
    api.post('/reports/export', payload, { responseType: 'blob' }),

  // Passports
  getChildPassport: (childId) => api.get(`/passports/child/${childId}`),
  getParentPassport: (parentId) => api.get(`/passports/parent/${parentId}`),

  // Quality Assurance & Audits
  getQATemplates: () => api.get('/qa/templates'),
  createQATemplate: (payload) => api.post('/qa/templates', payload),
  getQAAudits: (params = {}) => api.get('/qa/audits', { params }),
  createQAAudit: (payload) => api.post('/qa/audits', payload),
  getQAAuditDetail: (auditId) => api.get(`/qa/audits/${auditId}`),
  updateQAAudit: (auditId, payload) => api.put(`/qa/audits/${auditId}`, payload),
  getAuditTickler: () => api.get('/qa/tickler'),
  getQADashboard: () => api.get('/qa/dashboard'),

  // Custom User Dashboards
  getUserDashboardLayout: () => api.get('/dashboard/user-layout'),
  saveUserDashboardLayout: (layout) => api.post('/dashboard/layout', layout),
};
