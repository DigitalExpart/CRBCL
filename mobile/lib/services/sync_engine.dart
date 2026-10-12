import 'dart:convert';
import 'package:http/http.dart' as http;
import 'auth_service.dart';
import 'db_helper.dart';

class SyncProcessResult {
  final bool success;
  final int totalCount;
  final int syncedCount;
  final int failedCount;
  final int needsReviewCount;
  final String? errorMessage;

  SyncProcessResult({
    required this.success,
    this.totalCount = 0,
    this.syncedCount = 0,
    this.failedCount = 0,
    this.needsReviewCount = 0,
    this.errorMessage,
  });
}

class SyncEngine {
  final String? serverUrl;
  final String? authToken;

  SyncEngine({this.serverUrl, this.authToken});

  /// Push all pending and failed offline drafts to the backend
  Future<SyncProcessResult> pushPendingQueue() async {
    final authService = MobileAuthService.instance;
    final url = serverUrl ?? await authService.getServerUrl();
    final token = authToken ?? await authService.getAccessToken();
    final deviceId = await authService.getOrCreateDeviceId();

    if (token == null || token.isEmpty) {
      return SyncProcessResult(
        success: false,
        errorMessage: 'Authentication required. Please sign in before synchronizing.',
      );
    }

    final pendingDrafts = await LocalDatabaseHelper.instance.getPendingDrafts();
    if (pendingDrafts.isEmpty) {
      return SyncProcessResult(success: true, totalCount: 0);
    }

    final pushItems = <Map<String, dynamic>>[];
    for (var draft in pendingDrafts) {
      try {
        final payload = jsonDecode(draft['payload_json'] as String);
        pushItems.add({
          'client_mutation_id': draft['id'],
          'entity_type': draft['entity_type'],
          'payload': payload,
        });
      } catch (_) {
        // Skip malformed local payload
      }
    }

    if (pushItems.isEmpty) {
      return SyncProcessResult(success: true, totalCount: 0);
    }

    final pushPayload = {'items': pushItems};

    try {
      final pushUri = Uri.parse('$url/api/v1/sync/push');
      final response = await http.post(
        pushUri,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
          'X-Device-ID': deviceId,
        },
        body: jsonEncode(pushPayload),
      );

      if (response.statusCode == 401) {
        return SyncProcessResult(
          success: false,
          errorMessage: 'Session expired. Please log in with your CRBCL credentials to re-authenticate.',
        );
      }

      if (response.statusCode == 403) {
        String detail = 'Access forbidden. This device may be revoked by an administrator.';
        try {
          final body = jsonDecode(response.body);
          if (body['detail'] != null) detail = body['detail'].toString();
        } catch (_) {}
        return SyncProcessResult(success: false, errorMessage: detail);
      }

      if (response.statusCode != 200) {
        return SyncProcessResult(
          success: false,
          errorMessage: 'Server returned error status ${response.statusCode}',
        );
      }

      final resData = jsonDecode(response.body);
      final processedItems = resData['items'] as List<dynamic>? ?? [];

      int synced = 0;
      int failed = 0;
      int needsReview = 0;

      for (var item in processedItems) {
        final mutationId = item['client_mutation_id'] as String? ?? '';
        final status = (item['status'] as String? ?? '').toUpperCase();
        final serverId = item['server_id'] as String?;
        final personIdNumber = item['person_id_number'] as String?;
        final referralNumber = item['referral_number'] as String?;
        final error = item['error'] as String? ?? item['message'] as String?;

        if (status == 'SUCCESS' || status == 'ALREADY_PROCESSED') {
          synced++;
          await LocalDatabaseHelper.instance.updateDraftSyncResult(
            id: mutationId,
            status: 'SYNCED',
            serverId: serverId,
            personIdNumber: personIdNumber,
            referralNumber: referralNumber,
          );

          if (serverId != null) {
            final draft = pendingDrafts.firstWhere((d) => d['id'] == mutationId, orElse: () => {});
            final entityType = (draft['entity_type'] as String?) ?? 'UNKNOWN';
            await LocalDatabaseHelper.instance.recordIdMapping(
              tempId: mutationId,
              serverId: serverId,
              entityType: entityType,
            );
          }
        } else if (status == 'NEEDS_REVIEW') {
          needsReview++;
          final candidatesStr = item['candidates'] != null ? jsonEncode(item['candidates']) : null;
          await LocalDatabaseHelper.instance.updateDraftSyncResult(
            id: mutationId,
            status: 'NEEDS_REVIEW',
            errorMessage: 'Potential duplicate Person record detected. Review candidates: $candidatesStr',
          );
        } else {
          failed++;
          await LocalDatabaseHelper.instance.updateDraftSyncResult(
            id: mutationId,
            status: 'FAILED',
            errorMessage: error ?? 'Sync error: $status',
          );
        }
      }

      // Record successful synchronization timestamp
      await authService.touchAuthTimestamp();

      return SyncProcessResult(
        success: true,
        totalCount: pushItems.length,
        syncedCount: synced,
        failedCount: failed,
        needsReviewCount: needsReview,
      );
    } catch (e) {
      return SyncProcessResult(
        success: false,
        errorMessage: 'Network error: Unable to connect to server. Records remain safe locally.',
      );
    }
  }
}
