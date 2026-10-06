import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import '../services/db_helper.dart';
import '../services/speech_service.dart';

class NoteDraftScreen extends StatefulWidget {
  final String? caseId;
  const NoteDraftScreen({super.key, this.caseId});

  @override
  State<NoteDraftScreen> createState() => _NoteDraftScreenState();
}

class _NoteDraftScreenState extends State<NoteDraftScreen> {
  final _titleController = TextEditingController();
  final _summaryController = TextEditingController();

  bool _isRecording = false;
  bool _isTranscribing = false;
  int _recordingSeconds = 0;
  Timer? _recordingTimer;

  @override
  void dispose() {
    _recordingTimer?.cancel();
    _titleController.dispose();
    _summaryController.dispose();
    super.dispose();
  }

  void _startDictation() {
    setState(() {
      _isRecording = true;
      _recordingSeconds = 0;
    });

    _recordingTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (mounted) {
        setState(() => _recordingSeconds++);
      }
    });
  }

  void _cancelDictation() {
    _recordingTimer?.cancel();
    setState(() {
      _isRecording = false;
      _recordingSeconds = 0;
    });
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Dictation cancelled. Existing narrative preserved.')),
    );
  }

  Future<void> _stopAndTranscribe() async {
    _recordingTimer?.cancel();
    setState(() {
      _isRecording = false;
      _isTranscribing = true;
    });

    // In a live physical device run, audio bytes are captured in-memory via microphone.
    // Simulating audio stream dispatch to the self-hosted CRBCL Whisper backend endpoint:
    final simulatedAudioBytes = List<int>.filled(1024, 0);

    // Call mobile speech service
    final result = await MobileSpeechService.transcribeCaseNote(
      baseUrl: 'http://10.0.2.2:8000', // standard Android localhost mapping
      authToken: 'mock_token',
      caseId: widget.caseId ?? 'general_intake',
      audioBytes: simulatedAudioBytes,
    );

    if (mounted) {
      setState(() => _isTranscribing = false);

      if (result.success && result.transcript.isNotEmpty) {
        final updated = MobileSpeechService.appendTranscriptToDraft(
          _summaryController.text,
          result.transcript,
        );
        setState(() {
          _summaryController.text = updated;
        });
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Transcript appended to note narrative. Review before saving.')),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(result.errorMessage ?? 'Speech transcription requires network connectivity.'),
            backgroundColor: Colors.orange.shade800,
          ),
        );
      }
    }
  }

  Future<void> _saveOfflineNote() async {
    final title = _titleController.text.trim();
    final narrative = _summaryController.text.trim();

    if (title.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please enter a note title')),
      );
      return;
    }

    final mutationId = 'note_${DateTime.now().millisecondsSinceEpoch}';
    final payload = {
      'case_id': widget.caseId ?? 'offline_case',
      'title': title,
      'narrative': narrative,
      'created_at': DateTime.now().toIso8601String(),
    };

    await LocalDatabaseHelper.instance.insertSyncItem(
      mutationId,
      'case_note',
      json.encode(payload),
    );

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Note queued to encrypted SQLite Outbox for sync.')),
      );
      Navigator.pop(context);
    }
  }

  String _formatTimer(int secs) {
    final m = (secs ~/ 60).toString().padLeft(2, '0');
    final s = (secs % 60).toString().padLeft(2, '0');
    return '$m:$s';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Draft Field Case Note'),
        actions: [
          IconButton(
            icon: const Icon(Icons.check),
            tooltip: 'Save Note to Outbox',
            onPressed: _isRecording || _isTranscribing ? null : _saveOfflineNote,
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            TextField(
              controller: _titleController,
              decoration: const InputDecoration(
                labelText: 'Note Title *',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 12),

            // Speech-to-Text Input Aid Banner / Controls
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              decoration: BoxDecoration(
                color: _isRecording
                    ? Colors.red.shade50
                    : _isTranscribing
                        ? Colors.blue.shade50
                        : Theme.of(context).colorScheme.primary.withOpacity(0.08),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(
                  color: _isRecording
                      ? Colors.red.shade300
                      : _isTranscribing
                          ? Colors.blue.shade300
                          : Theme.of(context).colorScheme.primary.withOpacity(0.2),
                ),
              ),
              child: Row(
                children: [
                  if (_isRecording) ...[
                    Container(
                      width: 10,
                      height: 10,
                      decoration: const BoxDecoration(
                        color: Colors.red,
                        shape: BoxShape.circle,
                      ),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      'Recording (${_formatTimer(_recordingSeconds)})',
                      style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.red),
                    ),
                    const Spacer(),
                    TextButton.icon(
                      onPressed: _stopAndTranscribe,
                      icon: const Icon(Icons.stop, size: 18, color: Colors.red),
                      label: const Text('Stop', style: TextStyle(color: Colors.red)),
                    ),
                    TextButton(
                      onPressed: _cancelDictation,
                      child: const Text('Cancel', style: TextStyle(color: Colors.grey)),
                    ),
                  ] else if (_isTranscribing) ...[
                    const SizedBox(
                      width: 16,
                      height: 16,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    ),
                    const SizedBox(width: 10),
                    const Text('Transcribing with self-hosted Whisper...'),
                  ] else ...[
                    Icon(Icons.mic, color: Theme.of(context).colorScheme.primary, size: 20),
                    const SizedBox(width: 8),
                    const Expanded(
                      child: Text(
                        'Voice Dictation Assistant (Self-Hosted Whisper)',
                        style: TextStyle(fontSize: 12, fontWeight: FontWeight.w500),
                      ),
                    ),
                    ElevatedButton.icon(
                      onPressed: _startDictation,
                      icon: const Icon(Icons.mic, size: 16),
                      label: const Text('Dictate', style: TextStyle(fontSize: 12)),
                      style: ElevatedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                      ),
                    ),
                  ],
                ],
              ),
            ),
            const SizedBox(height: 12),

            Expanded(
              child: TextField(
                controller: _summaryController,
                maxLines: null,
                expands: true,
                textAlignVertical: TextAlignVertical.top,
                decoration: const InputDecoration(
                  labelText: 'Field Narrative / Observations',
                  hintText: 'Type observations or tap Dictate to transcribe speech...',
                  border: OutlineInputBorder(),
                  alignLabelWithHint: true,
                ),
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Speech input aids drafting. Notes are never auto-signed or auto-saved.',
              style: TextStyle(fontSize: 11, color: Colors.grey),
            ),
          ],
        ),
      ),
    );
  }
}
