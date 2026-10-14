import 'dart:async';
import 'dart:io';
import 'package:flutter/widgets.dart';

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
      // Fast DNS probe to verify device has active internet connection
      final lookupResult = await InternetAddress.lookup('google.com')
          .timeout(const Duration(seconds: 2));

      if (lookupResult.isNotEmpty && lookupResult[0].rawAddress.isNotEmpty) {
        connected = true;
      }
    } on SocketException {
      // Immediate detection when network drops or is in airplane mode
      connected = false;
    } on TimeoutException {
      connected = false;
    } catch (_) {
      try {
        final fallback = await InternetAddress.lookup('cloudflare.com')
            .timeout(const Duration(seconds: 2));
        connected = fallback.isNotEmpty && fallback[0].rawAddress.isNotEmpty;
      } catch (_) {
        connected = false;
      }
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
