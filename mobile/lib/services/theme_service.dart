import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;

class CrbclPalette {
  final String key;
  final String label;
  final Color primary;
  final Color darkPrimary;

  const CrbclPalette({
    required this.key,
    required this.label,
    required this.primary,
    required this.darkPrimary,
  });
}

class MobileThemeService extends ChangeNotifier {
  static const _storageKey = 'crbcl_mobile_theme_prefs';
  static const _secureStorage = FlutterSecureStorage();

  static const List<CrbclPalette> palettes = [
    CrbclPalette(
      key: 'crbcl',
      label: 'CRBCL Crimson (Default)',
      primary: Color(0xFF8B2626),
      darkPrimary: Color(0xFFC44B4B),
    ),
    CrbclPalette(
      key: 'burgundy',
      label: 'Deep Burgundy',
      primary: Color(0xFF821D30),
      darkPrimary: Color(0xFFB83A52),
    ),
    CrbclPalette(
      key: 'earth',
      label: 'Warm Earth & Clay',
      primary: Color(0xFF9E4A22),
      darkPrimary: Color(0xFFD97241),
    ),
    CrbclPalette(
      key: 'forest',
      label: 'Evergreen & Sage',
      primary: Color(0xFF267344),
      darkPrimary: Color(0xFF3DA366),
    ),
    CrbclPalette(
      key: 'prairie',
      label: 'Prairie Sun & Gold',
      primary: Color(0xFFA57313),
      darkPrimary: Color(0xFFDCA432),
    ),
    CrbclPalette(
      key: 'ocean',
      label: 'Deep River Blue',
      primary: Color(0xFF245C99),
      darkPrimary: Color(0xFF4585D0),
    ),
    CrbclPalette(
      key: 'teal',
      label: 'Boreal Spruce Teal',
      primary: Color(0xFF217A6C),
      darkPrimary: Color(0xFF38B29E),
    ),
    CrbclPalette(
      key: 'neutral',
      label: 'Refined Slate',
      primary: Color(0xFF485669),
      darkPrimary: Color(0xFF7A8B9E),
    ),
    CrbclPalette(
      key: 'pink',
      label: 'Pink',
      primary: Color(0xFFD81B60),
      darkPrimary: Color(0xFFEC407A),
    ),
    CrbclPalette(
      key: 'light-pink',
      label: 'Light Pink',
      primary: Color(0xFFD45D82),
      darkPrimary: Color(0xFFF48FB1),
    ),
    CrbclPalette(
      key: 'purple',
      label: 'Purple',
      primary: Color(0xFF7B1FA2),
      darkPrimary: Color(0xFFA855F7),
    ),
    CrbclPalette(
      key: 'light-purple',
      label: 'Light Purple',
      primary: Color(0xFF8B5CF6),
      darkPrimary: Color(0xFFC4B5FD),
    ),
    CrbclPalette(
      key: 'sky-blue',
      label: 'Sky Blue',
      primary: Color(0xFF0284C7),
      darkPrimary: Color(0xFF38BDF8),
    ),
    CrbclPalette(
      key: 'yellow',
      label: 'Yellow',
      primary: Color(0xFFC27803),
      darkPrimary: Color(0xFFF59E0B),
    ),
  ];

  ThemeMode _themeMode = ThemeMode.system;
  String _accentKey = 'crbcl';
  String _density = 'comfortable';
  bool _highContrast = false;
  bool _reducedMotion = false;
  String? _defaultLandingDashboard;

  ThemeMode get themeMode => _themeMode;
  String get accentKey => _accentKey;
  String get density => _density;
  bool get highContrast => _highContrast;
  bool get reducedMotion => _reducedMotion;
  String? get defaultLandingDashboard => _defaultLandingDashboard;

  CrbclPalette get activePalette {
    return palettes.firstWhere(
      (p) => p.key == _accentKey,
      orElse: () => palettes.first,
    );
  }

  MobileThemeService() {
    _loadPreferences();
  }

  Future<void> _loadPreferences() async {
    try {
      final raw = await _secureStorage.read(key: _storageKey);
      if (raw != null) {
        final data = json.decode(raw);
        _applyParsedData(data);
        notifyListeners();
      }
    } catch (_) {
      // Use defaults if storage read fails
    }
  }

  void _applyParsedData(Map<String, dynamic> data) {
    if (data.containsKey('theme_mode')) {
      final modeStr = data['theme_mode'] as String?;
      if (modeStr == 'light') {
        _themeMode = ThemeMode.light;
      } else if (modeStr == 'dark') {
        _themeMode = ThemeMode.dark;
      } else {
        _themeMode = ThemeMode.system;
      }
    }
    if (data.containsKey('accent_theme')) {
      final raw = data['accent_theme'] as String?;
      final accent = raw?.replaceAll('_', '-');
      if (accent != null && palettes.any((p) => p.key == accent)) {
        _accentKey = accent;
      }
    }
    if (data.containsKey('density')) {
      _density = data['density'] == 'compact' ? 'compact' : 'comfortable';
    }
    if (data.containsKey('high_contrast')) {
      _highContrast = data['high_contrast'] == true;
    }
    if (data.containsKey('reduced_motion')) {
      _reducedMotion = data['reduced_motion'] == true;
    }
    if (data.containsKey('default_landing_dashboard')) {
      _defaultLandingDashboard = data['default_landing_dashboard'] as String?;
    }
  }

  Future<void> updatePreferences({
    ThemeMode? mode,
    String? accent,
    String? density,
    bool? highContrast,
    bool? reducedMotion,
    String? defaultLanding,
    String? authToken,
    String? backendUrl,
  }) async {
    if (mode != null) _themeMode = mode;
    if (accent != null) {
      final normalizedAccent = accent.replaceAll('_', '-');
      if (palettes.any((p) => p.key == normalizedAccent)) {
        _accentKey = normalizedAccent;
      }
    }
    if (density != null) _density = density;
    if (highContrast != null) _highContrast = highContrast;
    if (reducedMotion != null) _reducedMotion = reducedMotion;
    if (defaultLanding != null) _defaultLandingDashboard = defaultLanding;

    final jsonMap = {
      'theme_mode': _themeMode == ThemeMode.light
          ? 'light'
          : _themeMode == ThemeMode.dark
              ? 'dark'
              : 'system',
      'accent_theme': _accentKey,
      'density': _density,
      'high_contrast': _highContrast,
      'reduced_motion': _reducedMotion,
      'default_landing_dashboard': _defaultLandingDashboard,
    };

    await _secureStorage.write(key: _storageKey, value: json.encode(jsonMap));
    notifyListeners();

    // Sync to backend if token provided
    if (authToken != null && backendUrl != null) {
      try {
        final uri = Uri.parse('$backendUrl/api/v1/users/me/preferences');
        await http.put(
          uri,
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer $authToken',
          },
          body: json.encode({'appearance': jsonMap}),
        );
      } catch (_) {
        // Safe offline fallback
      }
    }
  }

  Future<void> syncWithBackend(String authToken, String backendUrl) async {
    try {
      final uri = Uri.parse('$backendUrl/api/v1/users/me/preferences');
      final res = await http.get(
        uri,
        headers: {'Authorization': 'Bearer $authToken'},
      );
      if (res.statusCode == 200) {
        final body = json.decode(res.body);
        if (body is Map<String, dynamic> && body.containsKey('appearance')) {
          _applyParsedData(body['appearance'] as Map<String, dynamic>);
          await _secureStorage.write(
            key: _storageKey,
            value: json.encode(body['appearance']),
          );
          notifyListeners();
        }
      }
    } catch (_) {
      // Offline fallback: retain local cached preferences
    }
  }

  ThemeData getLightTheme() {
    final palette = activePalette;
    final colorScheme = ColorScheme.fromSeed(
      seedColor: palette.primary,
      primary: palette.primary,
      brightness: Brightness.light,
    );

    return ThemeData(
      useMaterial3: true,
      colorScheme: colorScheme,
      scaffoldBackgroundColor: _highContrast ? Colors.white : const Color(0xFFF9F7F5),
      appBarTheme: AppBarTheme(
        backgroundColor: palette.primary,
        foregroundColor: Colors.white,
        elevation: _highContrast ? 2 : 0,
      ),
      cardTheme: CardThemeData(
        color: Colors.white,
        elevation: _highContrast ? 3 : 1,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(_density == 'compact' ? 6 : 12),
          side: _highContrast
              ? const BorderSide(color: Colors.black54, width: 1.5)
              : BorderSide.none,
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: palette.primary,
          foregroundColor: Colors.white,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(_density == 'compact' ? 6 : 10),
          ),
        ),
      ),
    );
  }

  ThemeData getDarkTheme() {
    final palette = activePalette;
    final colorScheme = ColorScheme.fromSeed(
      seedColor: palette.darkPrimary,
      primary: palette.darkPrimary,
      brightness: Brightness.dark,
    );

    return ThemeData(
      useMaterial3: true,
      colorScheme: colorScheme,
      scaffoldBackgroundColor: _highContrast ? Colors.black : const Color(0xFF141212),
      appBarTheme: AppBarTheme(
        backgroundColor: const Color(0xFF1F1C1C),
        foregroundColor: Colors.white,
        elevation: 0,
      ),
      cardTheme: CardThemeData(
        color: const Color(0xFF221E1E),
        elevation: 1,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(_density == 'compact' ? 6 : 12),
          side: _highContrast
              ? const BorderSide(color: Colors.white60, width: 1.5)
              : BorderSide.none,
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: palette.darkPrimary,
          foregroundColor: Colors.white,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(_density == 'compact' ? 6 : 10),
          ),
        ),
      ),
    );
  }
}
