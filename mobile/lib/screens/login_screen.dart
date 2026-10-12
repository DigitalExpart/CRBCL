import 'package:flutter/material.dart';
import '../services/auth_service.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _authService = MobileAuthService.instance;

  // Controllers
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _pinController = TextEditingController();
  final _newPinController = TextEditingController();
  final _confirmPinController = TextEditingController();
  final _serverUrlController = TextEditingController();

  bool _isLoading = true;
  bool _isOnlineLoginMode = false;
  bool _isSettingUpPin = false;
  bool _showAdvancedServerUrl = false;
  String? _statusMessage;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _checkInitialState();
  }

  Future<void> _checkInitialState() async {
    setState(() => _isLoading = true);
    final hasCreds = await _authService.hasSavedCredentials();
    final serverUrl = await _authService.getServerUrl();
    _serverUrlController.text = serverUrl;

    setState(() {
      _isOnlineLoginMode = !hasCreds;
      _isLoading = false;
    });
  }

  Future<void> _handleOnlineLogin() async {
    final email = _emailController.text.trim();
    final password = _passwordController.text;

    if (email.isEmpty || password.isEmpty) {
      setState(() => _errorMessage = 'Please enter both email and password.');
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
      _statusMessage = 'Connecting to CRBCL backend...';
    });

    final result = await _authService.loginOnline(
      email: email,
      password: password,
      serverUrl: _serverUrlController.text.trim(),
    );

    setState(() => _isLoading = false);

    if (!result.success) {
      setState(() => _errorMessage = result.errorMessage ?? 'Authentication failed');
      return;
    }

    if (result.requiresPinSetup) {
      setState(() {
        _isSettingUpPin = true;
        _statusMessage = 'Authentication successful! Please set your Quick Access PIN.';
      });
    } else {
      if (mounted) {
        Navigator.pushReplacementNamed(context, '/dashboard');
      }
    }
  }

  Future<void> _handleSetPin() async {
    final pin = _newPinController.text.trim();
    final confirm = _confirmPinController.text.trim();

    if (pin.length < 4 || pin.length > 6) {
      setState(() => _errorMessage = 'PIN must be 4 to 6 numeric digits.');
      return;
    }

    if (pin != confirm) {
      setState(() => _errorMessage = 'PINs do not match. Please re-enter.');
      return;
    }

    setState(() => _isLoading = true);
    final success = await _authService.setPin(pin);
    setState(() => _isLoading = false);

    if (success) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Quick Access PIN saved securely.')),
        );
        Navigator.pushReplacementNamed(context, '/dashboard');
      }
    } else {
      setState(() => _errorMessage = 'Failed to derive PBKDF2 key for PIN.');
    }
  }

  Future<void> _handlePinUnlock() async {
    final pin = _pinController.text.trim();
    if (pin.length < 4 || pin.length > 6) {
      setState(() => _errorMessage = 'Please enter a valid 4 or 6-digit PIN.');
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final result = await _authService.unlockWithPin(pin);
    setState(() => _isLoading = false);

    if (result.success) {
      if (mounted) {
        Navigator.pushReplacementNamed(context, '/dashboard');
      }
    } else {
      if (result.isExpired) {
        setState(() {
          _isOnlineLoginMode = true;
          _errorMessage = result.errorMessage;
        });
      } else {
        setState(() => _errorMessage = result.errorMessage);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Scaffold(
        backgroundColor: Colors.indigo.shade900,
        body: const Center(
          child: CircularProgressIndicator(color: Colors.white),
        ),
      );
    }

    return Scaffold(
      backgroundColor: Colors.indigo.shade900,
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 16.0),
            child: Card(
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              elevation: 8,
              child: Padding(
                padding: const EdgeInsets.all(24.0),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    // Header Brand
                    const Icon(Icons.shield, size: 56, color: Color(0xFF8B2626)),
                    const SizedBox(height: 12),
                    const Text(
                      'CRBCL Field Operations',
                      textAlign: TextAlign.center,
                      style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Colors.black87),
                    ),
                    const SizedBox(height: 4),
                    const Text(
                      'Cote First Nation Family Wellness',
                      textAlign: TextAlign.center,
                      style: TextStyle(fontSize: 13, color: Colors.black54),
                    ),
                    const SizedBox(height: 20),

                    // Error & Status Banners
                    if (_errorMessage != null) ...[
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: Colors.red.shade50,
                          borderRadius: BorderRadius.circular(8),
                          border: Border(left: BorderSide(color: Colors.red.shade700, width: 4)),
                        ),
                        child: Text(
                          _errorMessage!,
                          style: TextStyle(color: Colors.red.shade900, fontSize: 13),
                        ),
                      ),
                      const SizedBox(height: 16),
                    ],

                    if (_statusMessage != null) ...[
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: Colors.green.shade50,
                          borderRadius: BorderRadius.circular(8),
                          border: Border(left: BorderSide(color: Colors.green.shade700, width: 4)),
                        ),
                        child: Text(
                          _statusMessage!,
                          style: TextStyle(color: Colors.green.shade900, fontSize: 13),
                        ),
                      ),
                      const SizedBox(height: 16),
                    ],

                    // View Modes
                    if (_isSettingUpPin)
                      _buildPinSetupView()
                    else if (_isOnlineLoginMode)
                      _buildOnlineLoginView()
                    else
                      _buildPinUnlockView(),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildPinUnlockView() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const Text(
          'Quick Offline Access',
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 6),
        const Text(
          'Enter your personal PIN (PBKDF2-HMAC-SHA256 • 100k rounds)',
          style: TextStyle(fontSize: 12, color: Colors.black54),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 20),
        TextField(
          controller: _pinController,
          keyboardType: TextInputType.number,
          obscureText: true,
          maxLength: 6,
          decoration: const InputDecoration(
            labelText: 'Enter 4 or 6-digit PIN',
            prefixIcon: Icon(Icons.lock_outline),
            border: OutlineInputBorder(),
          ),
          onSubmitted: (_) => _handlePinUnlock(),
        ),
        const SizedBox(height: 12),
        ElevatedButton.icon(
          onPressed: _handlePinUnlock,
          icon: const Icon(Icons.lock_open),
          label: const Text('Unlock Vault'),
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFF8B2626),
            foregroundColor: Colors.white,
            padding: const EdgeInsets.symmetric(vertical: 14),
          ),
        ),
        const SizedBox(height: 16),
        TextButton(
          onPressed: () {
            setState(() {
              _isOnlineLoginMode = true;
              _errorMessage = null;
            });
          },
          child: const Text('Log in with CRBCL credentials instead'),
        ),
      ],
    );
  }

  Widget _buildOnlineLoginView() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const Text(
          'CRBCL Staff Sign In',
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 6),
        const Text(
          'Initial login requires active internet connection to authenticate and register device.',
          style: TextStyle(fontSize: 12, color: Colors.black54),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 16),
        TextField(
          controller: _emailController,
          keyboardType: TextInputType.emailAddress,
          decoration: const InputDecoration(
            labelText: 'Staff Email',
            prefixIcon: Icon(Icons.email_outlined),
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 12),
        TextField(
          controller: _passwordController,
          obscureText: true,
          decoration: const InputDecoration(
            labelText: 'Password',
            prefixIcon: Icon(Icons.key_outlined),
            border: OutlineInputBorder(),
          ),
          onSubmitted: (_) => _handleOnlineLogin(),
        ),
        const SizedBox(height: 12),

        // Server URL toggle for dev/testing
        InkWell(
          onTap: () => setState(() => _showAdvancedServerUrl = !_showAdvancedServerUrl),
          child: Row(
            children: [
              Icon(
                _showAdvancedServerUrl ? Icons.arrow_drop_down : Icons.arrow_right,
                color: Colors.grey.shade700,
              ),
              const Text('Server Connection Settings', style: TextStyle(fontSize: 12, color: Colors.black54)),
            ],
          ),
        ),
        if (_showAdvancedServerUrl) ...[
          const SizedBox(height: 8),
          TextField(
            controller: _serverUrlController,
            decoration: const InputDecoration(
              labelText: 'Backend URL',
              border: OutlineInputBorder(),
              isDense: true,
            ),
          ),
        ],

        const SizedBox(height: 16),
        ElevatedButton.icon(
          onPressed: _handleOnlineLogin,
          icon: const Icon(Icons.login),
          label: const Text('Authenticate & Register Device'),
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFF8B2626),
            foregroundColor: Colors.white,
            padding: const EdgeInsets.symmetric(vertical: 14),
          ),
        ),
        const SizedBox(height: 12),
        FutureBuilder<bool>(
          future: _authService.hasSavedCredentials(),
          builder: (context, snapshot) {
            if (snapshot.data == true) {
              return TextButton(
                onPressed: () {
                  setState(() {
                    _isOnlineLoginMode = false;
                    _errorMessage = null;
                  });
                },
                child: const Text('Switch back to Quick PIN Access'),
              );
            }
            return const SizedBox.shrink();
          },
        ),
      ],
    );
  }

  Widget _buildPinSetupView() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const Text(
          'Set Quick Access PIN',
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 6),
        const Text(
          'Create a 4 or 6-digit personal PIN for offline unlocking in the field.',
          style: TextStyle(fontSize: 12, color: Colors.black54),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 16),
        TextField(
          controller: _newPinController,
          keyboardType: TextInputType.number,
          obscureText: true,
          maxLength: 6,
          decoration: const InputDecoration(
            labelText: 'New PIN (4-6 digits)',
            prefixIcon: Icon(Icons.pin),
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 12),
        TextField(
          controller: _confirmPinController,
          keyboardType: TextInputType.number,
          obscureText: true,
          maxLength: 6,
          decoration: const InputDecoration(
            labelText: 'Confirm PIN',
            prefixIcon: Icon(Icons.check_circle_outline),
            border: OutlineInputBorder(),
          ),
          onSubmitted: (_) => _handleSetPin(),
        ),
        const SizedBox(height: 16),
        ElevatedButton.icon(
          onPressed: _handleSetPin,
          icon: const Icon(Icons.save),
          label: const Text('Save PIN & Enter App'),
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFF8B2626),
            foregroundColor: Colors.white,
            padding: const EdgeInsets.symmetric(vertical: 14),
          ),
        ),
      ],
    );
  }
}
