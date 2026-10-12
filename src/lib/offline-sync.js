/**
 * CRBCL Secure Offline Web Workspace — Synchronization Engine
 *
 * Implements non-disruptive, isolated synchronization of encrypted field drafts
 * directly to canonical backend sync endpoints (/api/v1/sync/push).
 */

import { OfflineDB } from './offline-db';
import { decryptData, encryptData } from './offline-crypto';
import { api } from '@/api';

const BACKEND_BASE = import.meta.env.VITE_API_URL || 'https://crbcl-production.up.railway.app';

export const OfflineSyncEngine = {
  /**
   * Test network connectivity and backend reachability
   */
  async checkConnectivity() {
    if (typeof navigator !== 'undefined' && !navigator.onLine) {
      return { isOnline: false, isBackendReachable: false };
    }

    try {
      const res = await fetch(`${BACKEND_BASE}/health`, {
        method: 'GET',
        cache: 'no-store',
      });
      const reachable = res.status === 200;
      return { isOnline: true, isBackendReachable: reachable };
    } catch (_) {
      return { isOnline: false, isBackendReachable: false };
    }
  },

  /**
   * Fetch backend synchronization configuration & eligibility
   */
  async getSyncConfig() {
    const token = api.auth.getToken();
    if (!token) return { offlineWebEnabled: false, userEligible: false };

    try {
      const res = await fetch(`${BACKEND_BASE}/api/v1/sync/config`, {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${token}`,
          'X-Client-Type': 'web',
        },
      });
      if (res.status === 200) {
        const data = await res.json();
        return {
          offlineWebEnabled: Boolean(data.offline_web_enabled),
          userEligible: Boolean(data.user_eligible),
          serverTime: data.server_time,
        };
      }
      return { offlineWebEnabled: false, userEligible: false };
    } catch (_) {
      return { offlineWebEnabled: false, userEligible: false };
    }
  },

  /**
   * Push pending offline drafts to canonical backend
   */
  async pushPendingDrafts(userId, cryptoKey) {
    if (!cryptoKey) {
      throw new Error('OFFLINE_WORKSPACE_LOCKED: Please unlock your workspace to synchronize drafts.');
    }

    const { isBackendReachable } = await this.checkConnectivity();
    if (!isBackendReachable) {
      throw new Error('BACKEND_UNREACHABLE: Cannot connect to CRBCL authoritative server. Drafts remain safely encrypted locally.');
    }

    const token = api.auth.getToken();
    if (!token) {
      throw new Error('AUTH_REQUIRED: Please log in to your CRBCL staff account to synchronize.');
    }

    // 1. Fetch pending and failed drafts
    const allDrafts = await OfflineDB.getDrafts(userId, 'ALL');
    const pendingDrafts = allDrafts.filter(
      (d) => d.syncStatus === 'WAITING_TO_SYNC' || d.syncStatus === 'FAILED'
    );

    if (pendingDrafts.length === 0) {
      return {
        success: true,
        totalProcessed: 0,
        syncedCount: 0,
        needsReviewCount: 0,
        failedCount: 0,
        message: 'All local drafts are already synchronized.',
      };
    }

    // 2. Decrypt payloads for push queue
    const pushItems = [];
    const draftMap = new Map();

    for (const draft of pendingDrafts) {
      try {
        const decryptedPayload = await decryptData(
          { iv: draft.iv, ciphertext: draft.ciphertext },
          cryptoKey
        );
        pushItems.push({
          client_mutation_id: draft.id,
          entity_type: draft.entityType,
          payload: decryptedPayload,
        });
        draftMap.set(draft.id, draft);
      } catch (err) {
        console.error(`Failed to decrypt draft ${draft.id} for sync:`, err);
        await OfflineDB.updateDraftStatus(draft.id, {
          syncStatus: 'FAILED',
          errorMessage: 'Decryption failed. Please verify your unlock passphrase.',
        });
      }
    }

    if (pushItems.length === 0) {
      throw new Error('DECRYPTION_FAILED: Unable to decrypt pending drafts.');
    }

    // 3. Post to canonical backend sync push endpoint
    const deviceId = `WEB-${String(userId || 'ANON').substring(0, 8)}-WORKSTATION`;
    const res = await fetch(`${BACKEND_BASE}/api/v1/sync/push`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
        'X-Device-ID': deviceId,
        'X-Client-Type': 'web',
      },
      body: JSON.stringify({ items: pushItems }),
    });

    if (res.status === 403) {
      const errData = await res.json().catch(() => ({}));
      const detail = errData.detail || 'Access forbidden: Web offline synchronization is disabled or unauthorized.';
      throw new Error(detail);
    }

    if (res.status === 401) {
      throw new Error('SESSION_EXPIRED: Your CRBCL session has expired. Please re-authenticate.');
    }

    if (!res.ok) {
      throw new Error(`SERVER_ERROR: Server returned HTTP status ${res.status}`);
    }

    const resData = await res.json();
    const results = resData.items || [];

    let syncedCount = 0;
    let needsReviewCount = 0;
    let failedCount = 0;

    for (const item of results) {
      const mutationId = item.client_mutation_id;
      const status = (item.status || '').toUpperCase();
      const serverId = item.server_id || null;
      const personIdNumber = item.person_id_number || null;
      const referralNumber = item.referral_number || null;
      const errorMsg = item.error || item.message || null;
      const candidates = item.candidates || null;

      const originalDraft = draftMap.get(mutationId);
      if (!originalDraft) continue;

      if (status === 'SUCCESS' || status === 'ALREADY_PROCESSED') {
        syncedCount++;
        await OfflineDB.updateDraftStatus(mutationId, {
          syncStatus: 'SYNCED',
          serverId: serverId,
          personIdNumber: personIdNumber,
          referralNumber: referralNumber,
          errorMessage: null,
        });

        if (serverId) {
          await OfflineDB.recordIdMapping(mutationId, serverId, originalDraft.entityType);
        }
      } else if (status === 'NEEDS_REVIEW') {
        needsReviewCount++;
        await OfflineDB.updateDraftStatus(mutationId, {
          syncStatus: 'NEEDS_REVIEW',
          candidates: candidates,
          errorMessage: errorMsg || 'Potential duplicate Person detected. Requires supervisor review.',
        });
      } else {
        failedCount++;
        await OfflineDB.updateDraftStatus(mutationId, {
          syncStatus: 'FAILED',
          errorMessage: errorMsg || `Synchronization failed with status ${status}.`,
        });
      }
    }

    return {
      success: true,
      totalProcessed: pushItems.length,
      syncedCount,
      needsReviewCount,
      failedCount,
      message: `Sync complete: ${syncedCount} synchronized, ${needsReviewCount} review required, ${failedCount} failed.`,
    };
  },
};
