import 'dart:convert';
import 'dart:math';
import 'package:crypto/crypto.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;

class AuthResult {
  final bool success;
  final String? errorMessage;
  final bool requiresPinSetup;
  final Map<String, dynamic>? user;

  AuthResult({
    required this.success,
    this.errorMessage,
    this.requiresPinSetup = false,
    this.user,
  });
}

class PinUnlockResult {
  final bool success;
  final bool isLocked;
  final bool isExpired;
  final String? errorMessage;
  final int remainingAttempts;

  PinUnlockResult({
    required this.success,
    this.isLocked = false,
    this.isExpired = false,
    this.errorMessage,
    this.remainingAttempts = 5,
  });
}

class MobileAuthService {
  static final MobileAuthService instance = MobileAuthService._internal();
  MobileAuthService._internal();

  static const _secureStorage = FlutterSecureStorage();

  // Storage Keys
  static const _keyAccessToken = 'crbcl_access_token';
  static const _keyRefreshToken = 'crbcl_refresh_token';
  static const _keyUserId = 'crbcl_user_id';
  static const _keyUserEmail = 'crbcl_user_email';
  static const _keyUserName = 'crbcl_user_name';
  static const _keyUserRoles = 'crbcl_user_roles';
  static const _keyUserPermissions = 'crbcl_user_permissions';
  static const _keyDeviceId = 'crbcl_device_id';
  static const _keyServerUrl = 'crbcl_server_url';
  static const _keyPinHash = 'crbcl_pin_hash';
  static const _keyPinSalt = 'crbcl_pin_salt';
  static const _keyLastAuthTime = 'crbcl_last_auth_time';
  static const _keyFailedAttempts = 'crbcl_pin_failed_attempts';
  static const _keyLockedUntil = 'crbcl_pin_locked_until';

  // Constants
  static const int pbkdf2Iterations = 100000;
  static const int maxFailedAttempts = 5;
  static const Duration lockoutDuration = Duration(minutes: 15);
  static const int offlineExpiryHours = 24;
  static const String defaultServerUrl = 'https://crbcl-production.up.railway.app';

  /// Derive PBKDF2 HMAC-SHA256 key from PIN and salt
  static String derivePbkdf2PinKey(String pin, String saltHex, {int iterations = pbkdf2Iterations}) {
    final salt = utf8.encode(saltHex);
    List<int> derivedKey = utf8.encode(pin);

    for (int i = 0; i < iterations; i++) {
      final hmac = Hmac(sha256, derivedKey);
      derivedKey = hmac.convert(salt).bytes;
    }
    return base64Url.encode(derivedKey);
  }

  /// Get or generate per-installation random 256-bit salt
  Future<String> getOrCreateSalt() async {
    String? salt = await _secureStorage.read(key: _keyPinSalt);
    if (salt == null) {
      final random = Random.secure();
      final values = List<int>.generate(32, (i) => random.nextInt(256));
      salt = base64Url.encode(values);
      await _secureStorage.write(key: _keyPinSalt, value: salt);
    }
    return salt;
  }

  /// Get or generate persistent unique device ID
  Future<String> getOrCreateDeviceId() async {
    String? deviceId = await _secureStorage.read(key: _keyDeviceId);
    if (deviceId == null) {
      final random = Random.secure();
      final randBytes = List<int>.generate(16, (i) => random.nextInt(256));
      deviceId = 'DEV-${base64Url.encode(randBytes).replaceAll('=', '').substring(0, 16)}';
      await _secureStorage.write(key: _keyDeviceId, value: deviceId);
    }
    return deviceId;
  }

  /// Check whether user has registered and set up a PIN on this device
  Future<bool> hasSavedCredentials() async {
    final token = await _secureStorage.read(key: _keyAccessToken);
    final pinHash = await _secureStorage.read(key: _keyPinHash);
    return token != null && pinHash != null;
  }

  /// Get stored server URL or fallback
  Future<String> getServerUrl() async {
    final url = await _secureStorage.read(key: _keyServerUrl);
    return url ?? defaultServerUrl;
  }

  /// Set server URL
  Future<void> setServerUrl(String url) async {
    await _secureStorage.write(key: _keyServerUrl, value: url.trim());
  }

  /// Perform first-time or refresh online authentication with backend
  Future<AuthResult> loginOnline({
    required String email,
    required String password,
    String? serverUrl,
  }) async {
    final effectiveUrl = (serverUrl ?? await getServerUrl()).replaceAll(RegExp(r'/+$'), '');
    await setServerUrl(effectiveUrl);

    try {
      final loginUri = Uri.parse('$effectiveUrl/api/v1/auth/login');
      final response = await http.post(
        loginUri,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'email': email.trim(),
          'password': password,
        }),
      );

      if (response.statusCode != 200) {
        String errorMsg = 'Authentication failed (HTTP ${response.statusCode})';
        try {
          final body = jsonDecode(response.body);
          if (body['detail'] != null) {
            if (body['detail'] is Map && body['detail']['error'] != null) {
              errorMsg = body['detail']['error']['message'] ?? errorMsg;
            } else if (body['detail'] is String) {
              errorMsg = body['detail'];
            }
          }
        } catch (_) {}
        return AuthResult(success: false, errorMessage: errorMsg);
      }

      final data = jsonDecode(response.body);
      final accessToken = data['access_token'] as String;
      final refreshToken = data['refresh_token'] as String?;
      final user = data['user'] as Map<String, dynamic>;

      final deviceId = await getOrCreateDeviceId();

      // Register device through existing device API
      final regUri = Uri.parse('$effectiveUrl/api/v1/sync/devices/register');
      final regResponse = await http.post(
        regUri,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $accessToken',
        },
        body: jsonEncode({
          'device_id': deviceId,
          'device_name': 'Caseworker Mobile Unit',
          'os_type': 'Android',
          'app_version': '1.0.0',
        }),
      );

      if (regResponse.statusCode != 200) {
        return AuthResult(
          success: false,
          errorMessage: 'Device registration failed (HTTP ${regResponse.statusCode}). Device might be revoked.',
        );
      }

      // Persist authentication material securely
      await _secureStorage.write(key: _keyAccessToken, value: accessToken);
      if (refreshToken != null) {
        await _secureStorage.write(key: _keyRefreshToken, value: refreshToken);
      }
      await _secureStorage.write(key: _keyUserId, value: user['id']?.toString() ?? '');
      await _secureStorage.write(key: _keyUserEmail, value: user['email']?.toString() ?? '');
      await _secureStorage.write(key: _keyUserName, value: user['display_name']?.toString() ?? '');
      await _secureStorage.write(key: _keyUserRoles, value: jsonEncode(user['roles'] ?? []));
      await _secureStorage.write(key: _keyUserPermissions, value: jsonEncode(user['permissions'] ?? []));
      await _secureStorage.write(key: _keyLastAuthTime, value: DateTime.now().toIso8601String());

      // Reset lockout state
      await _secureStorage.delete(key: _keyFailedAttempts);
      await _secureStorage.delete(key: _keyLockedUntil);

      final existingPin = await _secureStorage.read(key: _keyPinHash);
      return AuthResult(
        success: true,
        requiresPinSetup: existingPin == null,
        user: user,
      );
    } catch (e) {
      return AuthResult(
        success: false,
        errorMessage: 'Network error: Initial login requires an active internet connection.',
      );
    }
  }

  /// Set or update the user's personal 4 to 6-digit PIN
  Future<bool> setPin(String pin) async {
    if (pin.length < 4 || pin.length > 6) return false;
    final salt = await getOrCreateSalt();
    final pinHash = derivePbkdf2PinKey(pin, salt);
    await _secureStorage.write(key: _keyPinHash, value: pinHash);
    return true;
  }

  /// Unlock application offline using personal PIN
  Future<PinUnlockResult> unlockWithPin(String pin) async {
    // 1. Check lockout status
    final lockedUntilStr = await _secureStorage.read(key: _keyLockedUntil);
    if (lockedUntilStr != null) {
      final lockedUntil = DateTime.tryParse(lockedUntilStr);
      if (lockedUntil != null && DateTime.now().isBefore(lockedUntil)) {
        final remainingSecs = lockedUntil.difference(DateTime.now()).inSeconds;
        return PinUnlockResult(
          success: false,
          isLocked: true,
          errorMessage: 'App locked due to failed PIN attempts. Retry in $remainingSecs seconds.',
        );
      }
    }

    // 2. Check offline authorization expiry (24-hour limit)
    final lastAuthStr = await _secureStorage.read(key: _keyLastAuthTime);
    if (lastAuthStr != null) {
      final lastAuth = DateTime.tryParse(lastAuthStr);
      if (lastAuth != null) {
        final elapsedHours = DateTime.now().difference(lastAuth).inHours;
        if (elapsedHours >= offlineExpiryHours) {
          return PinUnlockResult(
            success: false,
            isExpired: true,
            errorMessage: 'Offline authorization expired ($elapsedHours hrs since last online sync). Please log in with your CRBCL credentials.',
          );
        }
      }
    }

    // 3. Verify PIN hash
    final salt = await getOrCreateSalt();
    final enteredHash = derivePbkdf2PinKey(pin, salt);
    final storedHash = await _secureStorage.read(key: _keyPinHash);

    if (storedHash != null && enteredHash == storedHash) {
      // Success: Clear lockout and failed attempts
      await _secureStorage.delete(key: _keyFailedAttempts);
      await _secureStorage.delete(key: _keyLockedUntil);
      return PinUnlockResult(success: true);
    }

    // Failure: Increment failed attempts
    final attemptsStr = await _secureStorage.read(key: _keyFailedAttempts);
    int failedAttempts = (attemptsStr != null ? int.tryParse(attemptsStr) ?? 0 : 0) + 1;
    await _secureStorage.write(key: _keyFailedAttempts, value: failedAttempts.toString());

    if (failedAttempts >= maxFailedAttempts) {
      final lockedUntil = DateTime.now().add(lockoutDuration);
      await _secureStorage.write(key: _keyLockedUntil, value: lockedUntil.toIso8601String());
      return PinUnlockResult(
        success: false,
        isLocked: true,
        errorMessage: 'Maximum PIN attempts exceeded. App locked for 15 minutes.',
        remainingAttempts: 0,
      );
    }

    final remaining = maxFailedAttempts - failedAttempts;
    return PinUnlockResult(
      success: false,
      errorMessage: 'Invalid PIN. $remaining attempt${remaining == 1 ? '' : 's'} remaining.',
      remainingAttempts: remaining,
    );
  }

  /// Get current access token
  Future<String?> getAccessToken() async {
    return await _secureStorage.read(key: _keyAccessToken);
  }

  /// Touch last auth time upon successful sync
  Future<void> touchAuthTimestamp() async {
    await _secureStorage.write(key: _keyLastAuthTime, value: DateTime.now().toIso8601String());
  }

  /// Get stored user metadata
  Future<Map<String, dynamic>> getCurrentUser() async {
    final id = await _secureStorage.read(key: _keyUserId);
    final email = await _secureStorage.read(key: _keyUserEmail);
    final name = await _secureStorage.read(key: _keyUserName);
    final rolesStr = await _secureStorage.read(key: _keyUserRoles);
    final permsStr = await _secureStorage.read(key: _keyUserPermissions);

    return {
      'id': id ?? '',
      'email': email ?? '',
      'name': name ?? '',
      'roles': rolesStr != null ? jsonDecode(rolesStr) : [],
      'permissions': permsStr != null ? jsonDecode(permsStr) : [],
    };
  }

  /// Clear all stored tokens and sessions
  Future<void> logout() async {
    await _secureStorage.delete(key: _keyAccessToken);
    await _secureStorage.delete(key: _keyRefreshToken);
    await _secureStorage.delete(key: _keyLastAuthTime);
  }
}
