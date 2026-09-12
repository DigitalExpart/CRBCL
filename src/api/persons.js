import { api } from './client';

/**
 * Resolve a sanitized, user-facing error message from a non-2xx response.
 * Maps known HTTP status codes to actionable messages.
 * Does NOT expose backend stack traces or database details.
 */
async function _extractError(res, fallback) {
  let body = {};
  try {
    body = await res.json();
  } catch {
    // unparseable body — use fallback
  }

  // Try nested error shapes used by this API
  const serverMsg =
    body?.error?.message ||
    body?.detail?.error?.message ||
    body?.detail?.message ||
    (typeof body?.detail === 'string' ? body.detail : null);

  switch (res.status) {
    case 409:
      return serverMsg || 'A person record with this information already exists (duplicate detected).';
    case 403:
      return 'You do not have permission to perform this action.';
    case 422:
      // Prefer the first field-level validation message if available
      if (Array.isArray(body?.detail)) {
        const first = body.detail[0];
        const field = first?.loc?.slice(1).join('.') || '';
        const msg = first?.msg || '';
        return field ? `Validation error on '${field}': ${msg}` : (msg || fallback);
      }
      return serverMsg || 'The submitted information is invalid. Please review the form and try again.';
    case 500:
    case 502:
    case 503:
      return 'A server error occurred. Please try again in a moment.';
    default:
      return serverMsg || fallback;
  }
}

export const personsApi = {
  list: async (params = {}) => {
    const query = new URLSearchParams();
    if (params.query) query.append('query', params.query);
    if (params.person_id_number) query.append('person_id_number', params.person_id_number);
    if (params.date_of_birth) query.append('date_of_birth', params.date_of_birth);
    if (params.limit) query.append('limit', params.limit);
    if (params.offset) query.append('offset', params.offset);
    const qs = query.toString();
    const res = await api.fetch(`/api/v1/persons${qs ? `?${qs}` : ''}`);
    if (!res.ok) {
      throw new Error(await _extractError(res, 'Failed to search persons.'));
    }
    return res.json();
  },

  getProfile: async (personId) => {
    const res = await api.fetch(`/api/v1/persons/${personId}`);
    if (!res.ok) {
      throw new Error(await _extractError(res, 'Failed to load person profile.'));
    }
    return res.json();
  },

  create: async (data) => {
    const res = await api.fetch('/api/v1/persons', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      throw new Error(await _extractError(res, 'Failed to create person.'));
    }
    return res.json();
  },

  update: async (personId, data) => {
    const res = await api.fetch(`/api/v1/persons/${personId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      throw new Error(await _extractError(res, 'Failed to update person.'));
    }
    return res.json();
  },

  /**
   * POST /api/v1/persons/duplicate-check
   * Returns duplicate candidates on 200; throws a sanitized Error on any non-2xx.
   * Previously this swallowed non-2xx and returned the error body as if it were
   * a successful candidate list — now fixed.
   */
  checkDuplicates: async (criteria) => {
    const res = await api.fetch('/api/v1/persons/duplicate-check', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(criteria),
    });
    if (!res.ok) {
      throw new Error(await _extractError(res, 'Duplicate check failed.'));
    }
    return res.json();
  },

  uploadPhoto: async (personId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await api.fetch(`/api/v1/persons/${personId}/photo`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      throw new Error(await _extractError(res, 'Photo upload failed.'));
    }
    return res.json();
  },
};
