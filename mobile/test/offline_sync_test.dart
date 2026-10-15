import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:crbcl_mobile/services/auth_service.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    FlutterSecureStorage.setMockInitialValues({});
  });

  group('MobileAuthService PBKDF2 & Cryptographic Tests', () {
    test('PBKDF2 HMAC-SHA256 derivation is deterministic given identical PIN and salt', () {
      const pin = '5678';
      const salt = 'random_cryptographic_salt_for_testing';

      final key1 = MobileAuthService.derivePbkdf2PinKey(pin, salt, iterations: 1000);
      final key2 = MobileAuthService.derivePbkdf2PinKey(pin, salt, iterations: 1000);

      expect(key1, isNotEmpty);
      expect(key1, equals(key2));
    });

    test('Different PINs or different salts produce different keys', () {
      const pin1 = '1122';
      const pin2 = '3344';
      const salt1 = 'salt_alpha';
      const salt2 = 'salt_beta';

      final keyA = MobileAuthService.derivePbkdf2PinKey(pin1, salt1, iterations: 500);
      final keyB = MobileAuthService.derivePbkdf2PinKey(pin2, salt1, iterations: 500);
      final keyC = MobileAuthService.derivePbkdf2PinKey(pin1, salt2, iterations: 500);

      expect(keyA, isNot(equals(keyB)));
      expect(keyA, isNot(equals(keyC)));
    });

    test('No hardcoded PIN 1234 or 123456 passes without explicit registration', () async {
      FlutterSecureStorage.setMockInitialValues({
        'crbcl_access_token': 'valid_token',
        'crbcl_pin_salt': 'test_salt_123',
      });

      // User sets their personal 6-digit PIN to 987654
      await MobileAuthService.instance.setPin('987654');

      // Attempting invalid length PIN or non-matching PIN must fail
      final result1234 = await MobileAuthService.instance.unlockWithPin('1234');
      expect(result1234.success, isFalse);

      final result123456 = await MobileAuthService.instance.unlockWithPin('123456');
      expect(result123456.success, isFalse);

      // Personal 6-digit PIN succeeds
      final validResult = await MobileAuthService.instance.unlockWithPin('987654');
      expect(validResult.success, isTrue);
    });

    test('Lockout triggered after 5 consecutive failed PIN attempts', () async {
      FlutterSecureStorage.setMockInitialValues({
        'crbcl_access_token': 'valid_token',
        'crbcl_pin_salt': 'test_salt_xyz',
      });
      await MobileAuthService.instance.setPin('889900');

      for (int i = 0; i < 4; i++) {
        final res = await MobileAuthService.instance.unlockWithPin('000000');
        expect(res.success, isFalse);
        expect(res.isLocked, isFalse);
      }

      // 5th attempt locks the application
      final fifthRes = await MobileAuthService.instance.unlockWithPin('000000');
      expect(fifthRes.success, isFalse);
      expect(fifthRes.isLocked, isTrue);
      expect(fifthRes.errorMessage, contains('Maximum PIN attempts exceeded'));
    });

    test('Offline authorization expiry enforced after 24 hours without online authentication', () async {
      final expiredTimestamp = DateTime.now().subtract(const Duration(hours: 25)).toIso8601String();

      FlutterSecureStorage.setMockInitialValues({
        'crbcl_access_token': 'valid_token',
        'crbcl_pin_salt': 'test_salt_time',
        'crbcl_last_auth_time': expiredTimestamp,
      });

      await MobileAuthService.instance.setPin('432100');

      // Unlocking with correct PIN must still be rejected due to 24-hr offline authorization expiry
      final result = await MobileAuthService.instance.unlockWithPin('432100');
      expect(result.success, isFalse);
      expect(result.isExpired, isTrue);
      expect(result.errorMessage, contains('Offline authorization expired'));
    });
  });
}
