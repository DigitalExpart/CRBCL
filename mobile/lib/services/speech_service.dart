import 'dart:convert';
import 'package:http/http.dart' as http;

class SpeechTranscriptionResult {
  final bool success;
  final String transcript;
  final String? errorMessage;
  final double durationSeconds;

  const SpeechTranscriptionResult({
    required this.success,
    required this.transcript,
    this.errorMessage,
    this.durationSeconds = 0.0,
  });
}

class MobileSpeechService {
  /// Transcribe audio recording for Case Note drafting assistance via self-hosted CRBCL Whisper.
  ///
  /// CRITICAL ARCHITECTURAL CONSTRAINTS:
  /// 1. Transcription NEVER auto-saves, signs, or creates a Case Note.
  /// 2. Audio is passed in-memory and never retained offline as an audio file.
  /// 3. Transcription strictly requires network connectivity to CRBCL backend.
  static Future<SpeechTranscriptionResult> transcribeCaseNote({
    required String baseUrl,
    required String authToken,
    required String caseId,
    required List<int> audioBytes,
    String? noteId,
    String purpose = 'case_note',
    String language = 'en',
  }) async {
    try {
      final uri = Uri.parse('$baseUrl/api/v1/cases/$caseId/notes/transcribe');
      final request = http.MultipartRequest('POST', uri);

      request.headers['Authorization'] = 'Bearer $authToken';
      request.fields['purpose'] = purpose;
      request.fields['language'] = language;
      if (noteId != null && noteId.isNotEmpty) {
        request.fields['note_id'] = noteId;
      }

      request.files.add(
        http.MultipartFile.fromBytes(
          'file',
          audioBytes,
          filename: 'dictation_${DateTime.now().millisecondsSinceEpoch}.m4a',
        ),
      );

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        final transcript = (data['transcript'] as String? ?? '').trim();
        final duration = (data['duration_seconds'] as num? ?? 0.0).toDouble();
        return SpeechTranscriptionResult(
          success: true,
          transcript: transcript,
          durationSeconds: duration,
        );
      } else {
        final err = _extractErrorMessage(response.body);
        return SpeechTranscriptionResult(
          success: false,
          transcript: '',
          errorMessage: err.isNotEmpty ? err : 'Transcription failed (HTTP ${response.statusCode})',
        );
      }
    } catch (e) {
      return const SpeechTranscriptionResult(
        success: false,
        transcript: '',
        errorMessage: 'Speech transcription requires an active network connection to CRBCL servers.',
      );
    }
  }

  /// Transcribe audio recording for Ask Red Bear prompt input assistance.
  static Future<SpeechTranscriptionResult> transcribeAskRedBear({
    required String baseUrl,
    required String authToken,
    required List<int> audioBytes,
    String language = 'en',
  }) async {
    try {
      final uri = Uri.parse('$baseUrl/api/v1/ask-red-bear/transcribe');
      final request = http.MultipartRequest('POST', uri);

      request.headers['Authorization'] = 'Bearer $authToken';
      request.fields['language'] = language;

      request.files.add(
        http.MultipartFile.fromBytes(
          'file',
          audioBytes,
          filename: 'ask_red_bear_${DateTime.now().millisecondsSinceEpoch}.m4a',
        ),
      );

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        final transcript = (data['transcript'] as String? ?? '').trim();
        final duration = (data['duration_seconds'] as num? ?? 0.0).toDouble();
        return SpeechTranscriptionResult(
          success: true,
          transcript: transcript,
          durationSeconds: duration,
        );
      } else {
        final err = _extractErrorMessage(response.body);
        return SpeechTranscriptionResult(
          success: false,
          transcript: '',
          errorMessage: err.isNotEmpty ? err : 'Transcription failed (HTTP ${response.statusCode})',
        );
      }
    } catch (e) {
      return const SpeechTranscriptionResult(
        success: false,
        transcript: '',
        errorMessage: 'Speech transcription requires an active network connection to CRBCL servers.',
      );
    }
  }

  /// Helper to append transcript to an existing draft preserving original text
  static String appendTranscriptToDraft(String existingDraft, String newTranscript) {
    if (newTranscript.isEmpty) return existingDraft;
    if (existingDraft.trim().isEmpty) return newTranscript.trim();
    return '${existingDraft.trimRight()}\n\n${newTranscript.trim()}';
  }

  static String _extractErrorMessage(String body) {
    try {
      final data = json.decode(body);
      if (data is Map) {
        if (data['error'] is Map && data['error']['message'] != null) {
          return data['error']['message'].toString();
        }
        if (data['detail'] is Map && data['detail']['message'] != null) {
          return data['detail']['message'].toString();
        }
        if (data['detail'] != null) {
          return data['detail'].toString();
        }
      }
    } catch (_) {}
    return '';
  }
}
