import 'dart:convert';
import 'package:http/http.dart' as http;
import 'db_helper.dart';

class SyncEngine {
  final String serverUrl;
  final String authToken;

  SyncEngine({required this.serverUrl, required this.authToken});

  Future<bool> pushPendingQueue() async {
    final pending = await LocalDatabaseHelper.instance.getPendingSyncItems();
    if (pending.isEmpty) return true;

    final pushPayload = {
      'items': pending.map((item) {
        return {
          'client_mutation_id': item['mutation_id'],
          'entity_type': item['entity_type'],
          'payload': jsonDecode(item['payload_json']),
        };
      }).toList(),
    };

    try {
      final response = await http.post(
        Uri.parse('$serverUrl/api/v1/sync/push'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $authToken',
        },
        body: jsonEncode(pushPayload),
      );

      if (response.statusCode == 200) {
        final resData = jsonDecode(response.body);
        final processedItems = resData['items'] as List;

        for (var item in processedItems) {
          final mutationId = item['client_mutation_id'];
          final status = item['status'];
          if (status == 'SUCCESS' || status == 'ALREADY_PROCESSED') {
            await LocalDatabaseHelper.instance.clearSyncedItem(mutationId);
          }
        }
        return true;
      }
    } catch (e) {
      // Offline or network error
      return false;
    }
    return false;
  }
}
