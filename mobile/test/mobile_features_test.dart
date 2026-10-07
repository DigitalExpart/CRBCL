import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:crbcl_mobile/services/theme_service.dart';
import 'package:crbcl_mobile/services/speech_service.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    FlutterSecureStorage.setMockInitialValues({});
  });

  group('MobileThemeService Unit Tests', () {
    test('Default theme preferences match CRBCL web baseline', () {
      final service = MobileThemeService();
      expect(service.themeMode, equals(ThemeMode.system));
      expect(service.accentKey, equals('crbcl'));
      expect(service.density, equals('comfortable'));
      expect(service.highContrast, isFalse);
      expect(service.reducedMotion, isFalse);
      expect(service.activePalette.primary, equals(const Color(0xFF8B2626)));
    });

    test('Updating accent palette changes active primary color', () async {
      final service = MobileThemeService();
      await service.updatePreferences(accent: 'forest');
      expect(service.accentKey, equals('forest'));
      expect(service.activePalette.primary, equals(const Color(0xFF267344)));

      await service.updatePreferences(accent: 'ocean');
      expect(service.accentKey, equals('ocean'));
      expect(service.activePalette.primary, equals(const Color(0xFF245C99)));

      await service.updatePreferences(accent: 'pink');
      expect(service.accentKey, equals('pink'));
      expect(service.activePalette.primary, equals(const Color(0xFFD81B60)));

      await service.updatePreferences(accent: 'light-pink');
      expect(service.accentKey, equals('light-pink'));
      expect(service.activePalette.primary, equals(const Color(0xFFD45D82)));

      await service.updatePreferences(accent: 'purple');
      expect(service.accentKey, equals('purple'));
      expect(service.activePalette.primary, equals(const Color(0xFF7B1FA2)));

      await service.updatePreferences(accent: 'light-purple');
      expect(service.accentKey, equals('light-purple'));
      expect(service.activePalette.primary, equals(const Color(0xFF8B5CF6)));

      await service.updatePreferences(accent: 'sky-blue');
      expect(service.accentKey, equals('sky-blue'));
      expect(service.activePalette.primary, equals(const Color(0xFF0284C7)));

      await service.updatePreferences(accent: 'yellow');
      expect(service.accentKey, equals('yellow'));
      expect(service.activePalette.primary, equals(const Color(0xFFC27803)));
    });

    test('ThemeData generation reflects light and dark modes', () {
      final service = MobileThemeService();
      final lightTheme = service.getLightTheme();
      final darkTheme = service.getDarkTheme();

      expect(lightTheme.brightness, equals(Brightness.light));
      expect(darkTheme.brightness, equals(Brightness.dark));
      expect(lightTheme.colorScheme.primary, equals(const Color(0xFF8B2626)));
    });

    test('High contrast mode alters scaffold background and card borders', () async {
      final service = MobileThemeService();
      await service.updatePreferences(highContrast: true);
      final lightTheme = service.getLightTheme();
      expect(lightTheme.scaffoldBackgroundColor, equals(Colors.white));
    });
  });

  group('MobileSpeechService Unit Tests', () {
    test('appendTranscriptToDraft appends to existing text without erasing draft', () {
      const existing = 'Initial case observations conducted with grandmother.';
      const transcript = 'Child was participating happily in cultural activity.';

      final combined = MobileSpeechService.appendTranscriptToDraft(existing, transcript);
      expect(combined, contains(existing));
      expect(combined, contains(transcript));
      expect(combined, equals('$existing\n\n$transcript'));
    });

    test('appendTranscriptToDraft handles empty existing draft cleanly', () {
      const transcript = 'Solo dictated note.';
      final result = MobileSpeechService.appendTranscriptToDraft('', transcript);
      expect(result, equals(transcript));
    });

    test('appendTranscriptToDraft preserves draft if transcript is empty', () {
      const existing = 'Existing typed notes.';
      final result = MobileSpeechService.appendTranscriptToDraft(existing, '');
      expect(result, equals(existing));
    });

    test('Offline speech failure returns clear network requirement message', () async {
      // Dispatched to non-existent endpoint
      final result = await MobileSpeechService.transcribeCaseNote(
        baseUrl: 'http://localhost:99999',
        authToken: 'invalid_token',
        caseId: 'test_case',
        audioBytes: [1, 2, 3],
      );

      expect(result.success, isFalse);
      expect(
        result.errorMessage,
        anyOf(
          contains('Speech transcription requires an active network connection'),
          contains('Transcription failed (HTTP 400)'),
        ),
      );
    });
  });
}
