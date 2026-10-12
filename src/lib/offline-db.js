/**
 * CRBCL Secure Offline Web Workspace — IndexedDB Storage Engine
 *
 * Implements isolated, user-partitioned local storage for encrypted drafts,
 * enrollment credentials, and server identifier mappings.
 */

const DB_NAME = 'crbcl_offline_workspace';
const DB_VERSION = 1;

let _dbPromise = null;

function openOfflineDatabase() {
  if (_dbPromise) return _dbPromise;

  _dbPromise = new Promise((resolve, reject) => {
    if (typeof window === 'undefined' || !window.indexedDB) {
      reject(new Error('INDEXED_DB_UNAVAILABLE: Browser does not support IndexedDB.'));
      return;
    }

    const request = window.indexedDB.open(DB_NAME, DB_VERSION);

    request.onupgradeneeded = (event) => {
      const db = event.target.result;

      // Drafts Store
      if (!db.objectStoreNames.contains('drafts')) {
        const draftsStore = db.createObjectStore('drafts', { keyPath: 'id' });
        draftsStore.createIndex('userId', 'userId', { unique: false });
        draftsStore.createIndex('syncStatus', 'syncStatus', { unique: false });
        draftsStore.createIndex('entityType', 'entityType', { unique: false });
        draftsStore.createIndex('userStatus', ['userId', 'syncStatus'], { unique: false });
      }

      // User Workspace Auth Store
      if (!db.objectStoreNames.contains('auth')) {
        db.createObjectStore('auth', { keyPath: 'userId' });
      }

      // ID Mapping Store
      if (!db.objectStoreNames.contains('id_mappings')) {
        db.createObjectStore('id_mappings', { keyPath: 'tempId' });
      }
    };

    request.onsuccess = (event) => {
      resolve(event.target.result);
    };

    request.onerror = (event) => {
      reject(event.target.error || new Error('Failed to open offline database'));
    };
  });

  return _dbPromise;
}

export const OfflineDB = {
  /**
   * Save or update an encrypted draft
   */
  async saveDraft(draftRecord) {
    const db = await openOfflineDatabase();
    return new Promise((resolve, reject) => {
      const tx = db.transaction('drafts', 'readwrite');
      const store = tx.objectStore('drafts');
      const record = {
        ...draftRecord,
        updatedAt: new Date().toISOString(),
      };
      const req = store.put(record);
      req.onsuccess = () => resolve(record);
      req.onerror = () => reject(req.error);
    });
  },

  /**
   * Get all encrypted drafts for a user, optionally filtered by sync status
   */
  async getDrafts(userId, statusFilter = 'ALL') {
    const db = await openOfflineDatabase();
    return new Promise((resolve, reject) => {
      const tx = db.transaction('drafts', 'readonly');
      const store = tx.objectStore('drafts');
      const index = store.index('userId');
      const req = index.getAll(userId);

      req.onsuccess = () => {
        let results = req.result || [];
        if (statusFilter && statusFilter !== 'ALL') {
          results = results.filter((d) => d.syncStatus === statusFilter);
        }
        // Sort newest first
        results.sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt));
        resolve(results);
      };
      req.onerror = () => reject(req.error);
    });
  },

  /**
   * Get single draft by ID
   */
  async getDraftById(id) {
    const db = await openOfflineDatabase();
    return new Promise((resolve, reject) => {
      const tx = db.transaction('drafts', 'readonly');
      const store = tx.objectStore('drafts');
      const req = store.get(id);
      req.onsuccess = () => resolve(req.result || null);
      req.onerror = () => reject(req.error);
    });
  },

  /**
   * Update draft status after sync operation
   */
  async updateDraftStatus(id, updates) {
    const db = await openOfflineDatabase();
    return new Promise((resolve, reject) => {
      const tx = db.transaction('drafts', 'readwrite');
      const store = tx.objectStore('drafts');
      const getReq = store.get(id);

      getReq.onsuccess = () => {
        const existing = getReq.result;
        if (!existing) {
          resolve(null);
          return;
        }
        const updated = {
          ...existing,
          ...updates,
          updatedAt: new Date().toISOString(),
        };
        const putReq = store.put(updated);
        putReq.onsuccess = () => resolve(updated);
        putReq.onerror = () => reject(putReq.error);
      };
      getReq.onerror = () => reject(getReq.error);
    });
  },

  /**
   * Delete draft by ID
   */
  async deleteDraft(id) {
    const db = await openOfflineDatabase();
    return new Promise((resolve, reject) => {
      const tx = db.transaction('drafts', 'readwrite');
      const store = tx.objectStore('drafts');
      const req = store.delete(id);
      req.onsuccess = () => resolve(true);
      req.onerror = () => reject(req.error);
    });
  },

  /**
   * Compute sync metrics for user dashboard
   */
  async getMetrics(userId) {
    const drafts = await this.getDrafts(userId, 'ALL');
    const counts = {
      TOTAL: drafts.length,
      WAITING_TO_SYNC: 0,
      SYNCED: 0,
      NEEDS_REVIEW: 0,
      FAILED: 0,
    };
    for (const d of drafts) {
      if (counts[d.syncStatus] !== undefined) {
        counts[d.syncStatus]++;
      }
    }
    return counts;
  },

  /**
   * Save or update user workspace auth metadata (salt, verifier)
   */
  async saveAuthMetadata(authData) {
    const db = await openOfflineDatabase();
    return new Promise((resolve, reject) => {
      const tx = db.transaction('auth', 'readwrite');
      const store = tx.objectStore('auth');
      const req = store.put(authData);
      req.onsuccess = () => resolve(authData);
      req.onerror = () => reject(req.error);
    });
  },

  /**
   * Get user workspace auth metadata
   */
  async getAuthMetadata(userId) {
    const db = await openOfflineDatabase();
    return new Promise((resolve, reject) => {
      const tx = db.transaction('auth', 'readonly');
      const store = tx.objectStore('auth');
      const req = store.get(userId);
      req.onsuccess = () => resolve(req.result || null);
      req.onerror = () => reject(req.error);
    });
  },

  /**
   * Record temporary-to-server ID mapping
   */
  async recordIdMapping(tempId, serverId, entityType) {
    const db = await openOfflineDatabase();
    return new Promise((resolve, reject) => {
      const tx = db.transaction('id_mappings', 'readwrite');
      const store = tx.objectStore('id_mappings');
      const req = store.put({
        tempId,
        serverId,
        entityType,
        createdAt: new Date().toISOString(),
      });
      req.onsuccess = () => resolve(true);
      req.onerror = () => reject(req.error);
    });
  },

  /**
   * Get mapped server ID
   */
  async getMappedServerId(tempId) {
    const db = await openOfflineDatabase();
    return new Promise((resolve, reject) => {
      const tx = db.transaction('id_mappings', 'readonly');
      const store = tx.objectStore('id_mappings');
      const req = store.get(tempId);
      req.onsuccess = () => resolve(req.result ? req.result.serverId : null);
      req.onerror = () => reject(req.error);
    });
  },
};
