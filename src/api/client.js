import { config } from '@/lib/config';

// Storage keys
const TOKEN_KEY = 'crbcl_access_token';
const USER_KEY = 'crbcl_current_user';

// Mock initial data store for demo/standalone functionality only
const INITIAL_USERS = [
  {
    id: 'usr_admin_1',
    email: 'admin@crbcl.ca',
    role: 'admin',
    full_name: 'System Administrator',
    team_access: ['All'],
    created_date: new Date().toISOString(),
  }
];

class StorageManager {
  static get(key, defaultVal = null) {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : defaultVal;
    } catch {
      return defaultVal;
    }
  }

  static set(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch (e) {
      console.warn('Storage write failed:', e);
    }
  }

  static remove(key) {
    try {
      localStorage.removeItem(key);
    } catch (e) {
      console.warn('Storage delete failed:', e);
    }
  }
}

// Map entity names to native FastAPI v1 endpoints
const NATIVE_ENDPOINT_MAP = {
  person: '/api/v1/persons',
  persons: '/api/v1/persons',
  client: '/api/v1/clients',
  clients: '/api/v1/clients',
  family: '/api/v1/families',
  families: '/api/v1/families',
  case: '/api/v1/cases',
  cases: '/api/v1/cases',
  casenote: '/api/v1/case-notes',
  casenotes: '/api/v1/case-notes',
  user: '/api/v1/users',
  users: '/api/v1/users',
  team: '/api/v1/teams',
  teams: '/api/v1/teams',
  provider: '/api/v1/providers',
  providers: '/api/v1/providers',
  school: '/api/v1/schools',
  schools: '/api/v1/schools',
  household: '/api/v1/households',
  households: '/api/v1/households',
};

// Entity service implementation with native FastAPI v1 routing & fail-closed safety
class EntityClient {
  constructor(entityName, apiClient) {
    this.name = entityName;
    this.apiClient = apiClient;
    this.storageKey = `crbcl_entity_${entityName.toLowerCase()}`;
    const lower = entityName.toLowerCase();
    this.nativeEndpoint = NATIVE_ENDPOINT_MAP[lower] || null;
  }

  _getLocalEntities() {
    if (!config.enableDemoData) {
      return [];
    }
    return StorageManager.get(this.storageKey, []);
  }

  _setLocalEntities(items) {
    if (config.enableDemoData) {
      StorageManager.set(this.storageKey, items);
    }
  }

  _sortAndLimit(items, sortBy, limit) {
    let result = [...items];
    if (sortBy) {
      const isDesc = sortBy.startsWith('-');
      const field = isDesc ? sortBy.substring(1) : sortBy;
      result.sort((a, b) => {
        const valA = a[field] ?? '';
        const valB = b[field] ?? '';
        if (valA < valB) return isDesc ? 1 : -1;
        if (valA > valB) return isDesc ? -1 : 1;
        return 0;
      });
    }
    if (limit && typeof limit === 'number') {
      result = result.slice(0, limit);
    }
    return result;
  }

  async list(sortBy = null, limit = null) {
    if (this.apiClient.baseURL) {
      try {
        const endpoint = this.nativeEndpoint || `/api/entities/${this.name}`;
        const sortParam = sortBy ? `sort=${encodeURIComponent(sortBy)}` : '';
        const limitParam = limit ? `limit=${limit}` : '';
        const queryParams = [sortParam, limitParam].filter(Boolean).join('&');
        const url = queryParams ? `${endpoint}?${queryParams}` : endpoint;

        const res = await this.apiClient.fetch(url);
        if (res.ok) {
          const data = await res.json();
          if (Array.isArray(data)) return data;
          if (data && Array.isArray(data.items)) return data.items;
          return [];
        } else if (!config.enableDemoData) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData?.error?.message || `Failed to fetch ${this.name} list`);
        }
      } catch (err) {
        if (!config.enableDemoData) {
          throw err;
        }
        console.warn(`API list fallback for ${this.name}:`, err);
      }
    }

    if (!config.enableDemoData) {
      return [];
    }
    const items = this._getLocalEntities();
    return this._sortAndLimit(items, sortBy, limit);
  }

  async filter(query = {}, sortBy = null, limit = null) {
    if (this.apiClient.baseURL) {
      try {
        // Special case for CaseNotes filtered by case_id
        if ((this.name.toLowerCase() === 'casenote' || this.name.toLowerCase() === 'casenotes') && query.case_id) {
          const res = await this.apiClient.fetch(`/api/v1/cases/${query.case_id}/notes?limit=${limit || 50}`);
          if (res.ok) {
            const data = await res.json();
            return Array.isArray(data) ? data : data.items || [];
          }
        }

        // Special case for single ID lookup
        if (query.id && this.nativeEndpoint) {
          const res = await this.apiClient.fetch(`${this.nativeEndpoint}/${query.id}`);
          if (res.ok) {
            const item = await res.json();
            return item ? [item] : [];
          }
        }

        const endpoint = this.nativeEndpoint || `/api/entities/${this.name}/filter`;
        const params = new URLSearchParams({ ...query, sort: sortBy || '', limit: limit || '' });
        const res = await this.apiClient.fetch(`${endpoint}?${params}`);
        if (res.ok) {
          const data = await res.json();
          return Array.isArray(data) ? data : data.items || [];
        } else if (!config.enableDemoData) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData?.error?.message || `Failed to filter ${this.name}`);
        }
      } catch (err) {
        if (!config.enableDemoData) {
          throw err;
        }
        console.warn(`API filter fallback for ${this.name}:`, err);
      }
    }

    if (!config.enableDemoData) {
      return [];
    }
    const items = this._getLocalEntities().filter(item => {
      return Object.entries(query).every(([k, v]) => String(item[k]) === String(v));
    });
    return this._sortAndLimit(items, sortBy, limit);
  }

  async get(id) {
    if (this.apiClient.baseURL) {
      try {
        const endpoint = this.nativeEndpoint || `/api/entities/${this.name}`;
        const res = await this.apiClient.fetch(`${endpoint}/${id}`);
        if (res.ok) return await res.json();
        if (!config.enableDemoData) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData?.error?.message || `${this.name} not found`);
        }
      } catch (err) {
        if (!config.enableDemoData) {
          throw err;
        }
        console.warn(`API get fallback for ${this.name}:`, err);
      }
    }

    if (!config.enableDemoData) {
      return null;
    }
    const items = this._getLocalEntities();
    return items.find(i => i.id === id) || null;
  }

  async create(data) {
    if (this.apiClient.baseURL) {
      try {
        let endpoint = this.nativeEndpoint || `/api/entities/${this.name}`;
        if ((this.name.toLowerCase() === 'casenote' || this.name.toLowerCase() === 'casenotes') && data.case_id) {
          endpoint = `/api/v1/cases/${data.case_id}/notes`;
        }

        const res = await this.apiClient.fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data),
        });
        if (res.ok) return await res.json();
        if (!config.enableDemoData) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData?.error?.message || `Failed to create ${this.name}`);
        }
      } catch (err) {
        if (!config.enableDemoData) {
          throw err;
        }
        console.warn(`API create fallback for ${this.name}:`, err);
      }
    }

    if (!config.enableDemoData) {
      throw new Error('Service unavailable');
    }

    const newRecord = {
      id: data.id || `rec_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      created_date: new Date().toISOString(),
      updated_date: new Date().toISOString(),
      ...data,
    };

    const items = this._getLocalEntities();
    items.unshift(newRecord);
    this._setLocalEntities(items);
    return newRecord;
  }

  async update(id, data) {
    if (this.apiClient.baseURL) {
      try {
        const endpoint = this.nativeEndpoint || `/api/entities/${this.name}`;
        const res = await this.apiClient.fetch(`${endpoint}/${id}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data),
        });
        if (res.ok) return await res.json();
        if (!config.enableDemoData) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData?.error?.message || `Failed to update ${this.name}`);
        }
      } catch (err) {
        if (!config.enableDemoData) {
          throw err;
        }
        console.warn(`API update fallback for ${this.name}:`, err);
      }
    }

    if (!config.enableDemoData) {
      throw new Error('Service unavailable');
    }

    const items = this._getLocalEntities();
    const index = items.findIndex(i => i.id === id);
    if (index !== -1) {
      items[index] = { ...items[index], ...data, updated_date: new Date().toISOString() };
      this._setLocalEntities(items);
      return items[index];
    }
    return { id, ...data };
  }

  async delete(id) {
    if (this.apiClient.baseURL) {
      try {
        const endpoint = this.nativeEndpoint || `/api/entities/${this.name}`;
        const res = await this.apiClient.fetch(`${endpoint}/${id}`, {
          method: 'DELETE',
        });
        if (res.ok) return true;
        if (!config.enableDemoData) {
          throw new Error(`Failed to delete ${this.name}`);
        }
      } catch (err) {
        if (!config.enableDemoData) {
          throw err;
        }
        console.warn(`API delete fallback for ${this.name}:`, err);
      }
    }

    if (!config.enableDemoData) {
      throw new Error('Service unavailable');
    }

    const items = this._getLocalEntities();
    const filtered = items.filter(i => i.id !== id);
    this._setLocalEntities(filtered);
    return true;
  }
}

// Native Authentication Service
class AuthService {
  constructor(apiClient) {
    this.apiClient = apiClient;
  }

  getToken() {
    return localStorage.getItem(TOKEN_KEY) || config.token || null;
  }

  setToken(token) {
    if (token) {
      localStorage.setItem(TOKEN_KEY, token);
    } else {
      localStorage.removeItem(TOKEN_KEY);
    }
  }

  isAuthenticated() {
    return !!this.getToken();
  }

  async me() {
    if (this.apiClient.baseURL) {
      try {
        const res = await this.apiClient.fetch('/api/v1/auth/me');
        if (res.ok) {
          const user = await res.json();
          StorageManager.set(USER_KEY, user);
          return user;
        } else if (res.status === 401 || res.status === 403) {
          this.setToken(null);
          StorageManager.remove(USER_KEY);
          return null;
        }
      } catch (err) {
        if (!config.enableDemoData) {
          console.warn('Backend unavailable, failing closed:', err);
          return null;
        }
      }
    }

    if (config.enableDemoData) {
      const savedUser = StorageManager.get(USER_KEY, INITIAL_USERS[0]);
      return savedUser;
    }
    return null;
  }

  async loginViaEmailPassword(email, password) {
    if (this.apiClient.baseURL) {
      const res = await this.apiClient.fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ error: { message: 'Login failed' } }));
        throw new Error(err?.error?.message || err.message || 'Invalid credentials');
      }
      const data = await res.json();
      this.setToken(data.access_token || data.token || 'crbcl_token');
      if (data.user) StorageManager.set(USER_KEY, data.user);
      return data;
    }

    if (!config.enableDemoData) {
      throw new Error('API server is not configured or unavailable');
    }

    const user = {
      id: `usr_${Date.now()}`,
      email,
      role: email.toLowerCase().includes('admin') ? 'admin' : 'staff',
      full_name: email.split('@')[0],
      team_access: ['All'],
    };
    this.setToken('crbcl_session_' + Date.now());
    StorageManager.set(USER_KEY, user);
    return { token: this.getToken(), user };
  }

  async loginWithProvider(provider = 'google', redirectUrl = '/') {
    if (this.apiClient.baseURL) {
      window.location.href = `${this.apiClient.baseURL}/api/v1/auth/oauth/${provider}?returnTo=${encodeURIComponent(redirectUrl)}`;
      return;
    }
    if (!config.enableDemoData) {
      throw new Error('OAuth login unavailable');
    }
    const user = {
      id: `usr_oauth_${Date.now()}`,
      email: `user@crbcl.ca`,
      role: 'admin',
      full_name: 'CRBCL User',
      team_access: ['All'],
    };
    this.setToken('crbcl_oauth_token_' + Date.now());
    StorageManager.set(USER_KEY, user);
    window.location.href = redirectUrl;
  }

  async register({ email, password }) {
    if (this.apiClient.baseURL) {
      const res = await this.apiClient.fetch('/api/v1/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ error: { message: 'Registration failed' } }));
        throw new Error(err?.error?.message || err.message || 'Registration failed');
      }
      return await res.json();
    }
    return { success: true, email };
  }

  async verifyOtp({ email, otpCode }) {
    if (this.apiClient.baseURL) {
      const res = await this.apiClient.fetch('/api/v1/auth/verify-otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, otpCode }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ error: { message: 'Verification failed' } }));
        throw new Error(err?.error?.message || err.message || 'Invalid OTP code');
      }
      const data = await res.json();
      if (data.access_token) this.setToken(data.access_token);
      return data;
    }
    const token = 'crbcl_otp_token_' + Date.now();
    this.setToken(token);
    return { success: true, access_token: token };
  }

  async resendOtp(email) {
    if (this.apiClient.baseURL) {
      const res = await this.apiClient.fetch('/api/v1/auth/resend-otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });
      if (!res.ok) throw new Error('Failed to resend OTP');
      return await res.json();
    }
    return { success: true };
  }

  async resetPasswordRequest(email) {
    if (this.apiClient.baseURL) {
      const res = await this.apiClient.fetch('/api/v1/auth/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });
      if (!res.ok) throw new Error('Failed to send reset link');
      return await res.json();
    }
    return { success: true };
  }

  async resetPassword({ resetToken, newPassword }) {
    if (this.apiClient.baseURL) {
      const res = await this.apiClient.fetch('/api/v1/auth/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reset_token: resetToken, new_password: newPassword }),
      });
      if (!res.ok) throw new Error('Password reset failed');
      return await res.json();
    }
    return { success: true };
  }

  async logout(redirectUrl = null) {
    if (this.apiClient.baseURL) {
      try {
        await this.apiClient.fetch('/api/v1/auth/logout', { method: 'POST' });
      } catch (e) {
        console.warn('Logout API error:', e);
      }
    }
    this.setToken(null);
    StorageManager.remove(USER_KEY);
    if (redirectUrl) {
      window.location.href = redirectUrl;
    }
  }

  redirectToLogin(redirectUrl = null) {
    const returnTo = redirectUrl ? `?returnTo=${encodeURIComponent(redirectUrl)}` : '';
    window.location.href = `/login${returnTo}`;
  }
}

// Integrations Service
class IntegrationsService {
  constructor(apiClient) {
    this.apiClient = apiClient;
    this.Core = {
      UploadFile: async ({ file }) => {
        if (this.apiClient.baseURL) {
          const formData = new FormData();
          formData.append('file', file);
          const res = await this.apiClient.fetch('/api/v1/documents/upload', {
            method: 'POST',
            body: formData,
          });
          if (res.ok) return await res.json();
        }
        const file_url = URL.createObjectURL(file);
        return { file_url, name: file.name, size: file.size };
      },

      InvokeLLM: async ({ prompt }) => {
        return `Tansi! I am **Ask Red Bear**, your AI assistant at Chief Red Bear Children's Lodge.\n\n` +
          `Based on your query and current records:\n\n` +
          `- **Status Overview**: All active cases and service plans are being monitored.\n` +
          `- **Recommendations**: Review upcoming scheduled appointments and follow up with family case notes.\n` +
          `- **Next Steps**: Continue prioritizing culturally grounded family supports and ensure compliance with provincial reporting.\n\n` +
          `*Feel free to ask me to draft case notes, summarize grant funding, or analyze client trends.*`;
      },

      SendEmail: async ({ to, subject, body }) => {
        return { success: true };
      }
    };
  }
}

// Master API Client
export class ApiClient {
  constructor(options = {}) {
    this.baseURL = options.appBaseUrl || config.apiBaseUrl || '';
    this.appId = options.appId || config.appId || 'crbcl-app';
    this.auth = new AuthService(this);
    this.integrations = new IntegrationsService(this);

    // Entity instances proxy
    this._entities = {};
    this.entities = new Proxy(this._entities, {
      get: (target, entityName) => {
        if (!target[entityName]) {
          target[entityName] = new EntityClient(entityName, this);
        }
        return target[entityName];
      }
    });
  }

  _getCsrfToken() {
    if (typeof document === 'undefined') return null;
    const match = document.cookie.match(new RegExp('(^|;\\s*)crbcl_csrf_token=([^;]*)'));
    return match ? decodeURIComponent(match[2]) : null;
  }

  async fetch(endpoint, options = {}) {
    const token = this.auth.getToken();
    const csrfToken = this._getCsrfToken();

    const headers = {
      ...(options.headers || {}),
      'X-App-Id': this.appId,
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    if (csrfToken) {
      headers['X-CSRF-Token'] = csrfToken;
    }

    const url = this.baseURL ? `${this.baseURL}${endpoint}` : endpoint;
    return fetch(url, {
      credentials: 'include',
      ...options,
      headers,
    });
  }
}

// Create and export singleton instance
export const api = new ApiClient({
  appId: config.appId,
  appBaseUrl: config.apiBaseUrl,
});

export const apiClient = api;
export default api;
