import { api } from './client';

export const caseNotesApi = {
  listForCase: (caseId, limit = 50) => api.entities.CaseNote.filter({ case_id: caseId }, '-created_date', limit),
  get: (id) => api.entities.CaseNote.get(id),
  create: (data) => api.entities.CaseNote.create(data),
  update: (id, data) => api.entities.CaseNote.update(id, data),
  delete: (id) => api.entities.CaseNote.delete(id),
};
