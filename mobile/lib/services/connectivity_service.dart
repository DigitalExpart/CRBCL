import 'dart:async';
import 'dart:io';
import 'package:flutter/widgets.dart';
import 'package:http/http.dart' as http;
import 'auth_service.dart';

/// Real-time service monitoring device network and CRBCL backend connectivity.
class ConnectivityService extends ChangeNotifier {
  static final ConnectivityService instance = ConnectivityService._init();

  bool _isOnline = true;
  Timer? _pollingTimer;
  bool _isChecking = false;

  ConnectivityService._init() {
    _startPeriodicChecks();
  }

  bool get isOnline => _isOnline;

  void _startPeriodicChecks() {
    // Avoid active polling timers during widget tests
    if (WidgetsBinding.instance.runtimeType.toString().contains('Test')) {
      _isOnline = false;
      return;
    }

    // Initial check immediately on service initialization
    checkConnectivity();

    // Check periodically every 5 seconds for real-time responsiveness
    _pollingTimer = Timer.periodic(const Duration(seconds: 5), (_) {
      checkConnectivity();
    });
  }

  /// Perform active connectivity probe using DNS lookup + backend /api/v1/health probe.
  Future<bool> checkConnectivity() async {
    if (WidgetsBinding.instance.runtimeType.toString().contains('Test')) {
      return _isOnline;
    }

    if (_isChecking) return _isOnline;
    _isChecking = true;

    bool connected = false;

    try {
      // 1. Fast DNS/Socket probe for physical network connectivity
      final lookupResult = await InternetAddress.lookup('crbcl-production.up.railway.app')
          .timeout(const Duration(seconds: 2));

      if (lookupResult.isNotEmpty && lookupResult[0].rawAddress.isNotEmpty) {
        // 2. Active backend API health probe
        final serverUrl = await MobileAuthService.instance.getServerUrl();
        final uri = Uri.parse('$serverUrl/api/v1/health');
        final response = await http.get(uri).timeout(const Duration(seconds: 3));

        if (response.statusCode == 200) {
          connected = true;
        }
      }
    } on SocketException {
      // Immediate detection when network interface drops or is in airplane mode
      connected = false;
    } on TimeoutException {
      connected = false;
    } catch (_) {
      connected = false;
    } finally {
      _isChecking = false;
    }

    if (_isOnline != connected) {
      _isOnline = connected;
      notifyListeners();
    }

    return _isOnline;
  }

  /// Manually force a status update (e.g. for unit tests)
  void setOnlineForTesting(bool value) {
    _isOnline = value;
    notifyListeners();
  }

  @override
  void dispose() {
    _pollingTimer?.cancel();
    super.dispose();
  }
}
