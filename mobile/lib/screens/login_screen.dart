import 'package:flutter/material.dart';
import '../services/auth_service.dart';
import '../services/theme_service.dart';
import '../widgets/crbcl_logo.dart';

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

  bool _isLoading = true;
  bool _isOnlineLoginMode = false;
  bool _isSettingUpPin = false;

  // Visibility toggles (hidden by default)
  bool _obscurePassword = true;
  bool _obscurePin = true;
  bool _obscureNewPin = true;
  bool _obscureConfirmPin = true;

  String? _statusMessage;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _checkInitialState();
  }

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    _pinController.dispose();
    _newPinController.dispose();
    _confirmPinController.dispose();
    super.dispose();
  }

  Future<void> _checkInitialState() async {
    setState(() => _isLoading = true);
    final hasCreds = await _authService.hasSavedCredentials();

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
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;
    final isDark = theme.brightness == Brightness.dark;

    if (_isLoading) {
      return Scaffold(
        body: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const CrbclLogo(height: 56, variant: CrbclLogoVariant.emblem),
              const SizedBox(height: 24),
              CircularProgressIndicator(color: colorScheme.primary),
              const SizedBox(height: 12),
              Text(
                'Securing Connection...',
                style: TextStyle(
                  fontSize: 13,
                  color: colorScheme.onSurface.withValues(alpha: 0.7),
                ),
              ),
            ],
          ),
        ),
      );
    }

    return Scaffold(
      backgroundColor: isDark
          ? colorScheme.surface
          : const Color(0xFFF7F5F2),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 20.0),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 440),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Official CRBCL Brand Header
                  Center(
                    child: Column(
                      children: [
                        const CrbclLogo(
                          height: 72,
                          variant: CrbclLogoVariant.emblem,
                        ),
                        const SizedBox(height: 12),
                        Text(
                          'CRBCL Field Operations',
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            fontFamily: CrbclTokens.fontHeading,
                            fontSize: 22,
                            fontWeight: FontWeight.bold,
                            color: colorScheme.onSurface,
                            letterSpacing: 0.2,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          'Cote First Nation Family Wellness',
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            fontSize: 13,
                            color: colorScheme.onSurface.withValues(alpha: 0.65),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 24),

                  // Login / Unlock Card
                  Card(
                    elevation: isDark ? 0 : 3,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16),
                      side: BorderSide(
                        color: isDark ? colorScheme.outlineVariant : Colors.black12,
                        width: 1,
                      ),
                    ),
                    color: colorScheme.surfaceContainer,
                    child: Padding(
                      padding: const EdgeInsets.all(24.0),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          // Error Banner
                          if (_errorMessage != null) ...[
                            Container(
                              padding: const EdgeInsets.all(12),
                              decoration: BoxDecoration(
                                color: colorScheme.error.withValues(alpha: 0.12),
                                borderRadius: BorderRadius.circular(8),
                                border: Border(
                                  left: BorderSide(color: colorScheme.error, width: 4),
                                ),
                              ),
                              child: Row(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Icon(Icons.error_outline, size: 18, color: colorScheme.error),
                                  const SizedBox(width: 8),
                                  Expanded(
                                    child: Text(
                                      _errorMessage!,
                                      style: TextStyle(
                                        color: isDark ? CrbclTokens.statusErrorDark : CrbclTokens.statusError,
                                        fontSize: 13,
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            const SizedBox(height: 16),
                          ],

                          // Status Message Banner
                          if (_statusMessage != null) ...[
                            Container(
                              padding: const EdgeInsets.all(12),
                              decoration: BoxDecoration(
                                color: CrbclTokens.statusSuccess.withValues(alpha: 0.12),
                                borderRadius: BorderRadius.circular(8),
                                border: const Border(
                                  left: BorderSide(color: CrbclTokens.statusSuccess, width: 4),
                                ),
                              ),
                              child: Row(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Icon(Icons.check_circle_outline, size: 18, color: CrbclTokens.statusSuccess),
                                  const SizedBox(width: 8),
                                  Expanded(
                                    child: Text(
                                      _statusMessage!,
                                      style: TextStyle(
                                        color: isDark ? CrbclTokens.statusSuccessDark : CrbclTokens.statusSuccess,
                                        fontSize: 13,
                                      ),
                                    ),
                                  ),
                                ],
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

                  // Footer security badge
                  const SizedBox(height: 16),
                  Center(
                    child: Wrap(
                      alignment: WrapAlignment.center,
                      crossAxisAlignment: WrapCrossAlignment.center,
                      spacing: 6,
                      children: [
                        Icon(
                          Icons.verified_user_outlined,
                          size: 14,
                          color: colorScheme.onSurface.withValues(alpha: 0.5),
                        ),
                        Text(
                          'Encrypted Offline-First Field Platform',
                          style: TextStyle(
                            fontSize: 11,
                            color: colorScheme.onSurface.withValues(alpha: 0.5),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildPinUnlockView() {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          'Quick Offline Access',
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.w600,
            color: colorScheme.onSurface,
          ),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 6),
        Text(
          'Enter your personal PIN (PBKDF2-HMAC-SHA256 • 100k rounds)',
          style: TextStyle(
            fontSize: 12,
            color: colorScheme.onSurface.withValues(alpha: 0.65),
          ),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 20),

        TextField(
          controller: _pinController,
          keyboardType: TextInputType.number,
          obscureText: _obscurePin,
          maxLength: 6,
          decoration: InputDecoration(
            labelText: 'Enter 4 or 6-digit PIN',
            prefixIcon: const Icon(Icons.lock_outline),
            suffixIcon: IconButton(
              icon: Icon(
                _obscurePin ? Icons.visibility_off : Icons.visibility,
                semanticLabel: _obscurePin ? 'Show PIN' : 'Hide PIN',
              ),
              onPressed: () {
                setState(() => _obscurePin = !_obscurePin);
              },
            ),
            border: const OutlineInputBorder(),
          ),
          onSubmitted: (_) => _handlePinUnlock(),
        ),
        const SizedBox(height: 12),

        ElevatedButton(
          onPressed: _handlePinUnlock,
          style: ElevatedButton.styleFrom(
            backgroundColor: colorScheme.primary,
            foregroundColor: colorScheme.onPrimary,
            padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 12),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            mainAxisSize: MainAxisSize.min,
            children: const [
              Icon(Icons.lock_open),
              SizedBox(width: 8),
              Flexible(
                child: Text(
                  'Unlock Vault',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
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
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          'CRBCL Staff Sign In',
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.w600,
            color: colorScheme.onSurface,
          ),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 6),
        Text(
          'Initial login requires active internet connection to authenticate and register device.',
          style: TextStyle(
            fontSize: 12,
            color: colorScheme.onSurface.withValues(alpha: 0.65),
          ),
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
        const SizedBox(height: 14),

        TextField(
          controller: _passwordController,
          obscureText: _obscurePassword,
          decoration: InputDecoration(
            labelText: 'Password',
            prefixIcon: const Icon(Icons.key_outlined),
            suffixIcon: IconButton(
              icon: Icon(
                _obscurePassword ? Icons.visibility_off : Icons.visibility,
                semanticLabel: _obscurePassword ? 'Show password' : 'Hide password',
              ),
              onPressed: () {
                setState(() => _obscurePassword = !_obscurePassword);
              },
            ),
            border: const OutlineInputBorder(),
          ),
          onSubmitted: (_) => _handleOnlineLogin(),
        ),
        const SizedBox(height: 12),

        const SizedBox(height: 16),
        ElevatedButton(
          onPressed: _handleOnlineLogin,
          style: ElevatedButton.styleFrom(
            backgroundColor: colorScheme.primary,
            foregroundColor: colorScheme.onPrimary,
            padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 12),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            mainAxisSize: MainAxisSize.min,
            children: const [
              Icon(Icons.login),
              SizedBox(width: 8),
              Flexible(
                child: Text(
                  'Authenticate & Register Device',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 14),

        // New Sign Up link
        Wrap(
          alignment: WrapAlignment.center,
          crossAxisAlignment: WrapCrossAlignment.center,
          children: [
            Text(
              "Don't have an account? ",
              style: TextStyle(
                fontSize: 13,
                color: colorScheme.onSurface.withValues(alpha: 0.7),
              ),
            ),
            GestureDetector(
              onTap: () => Navigator.pushNamed(context, '/signup'),
              child: Text(
                'Sign Up',
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.bold,
                  color: colorScheme.primary,
                ),
              ),
            ),
          ],
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
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          'Set Quick Access PIN',
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.w600,
            color: colorScheme.onSurface,
          ),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 6),
        Text(
          'Create a 4 or 6-digit personal PIN for offline unlocking in the field.',
          style: TextStyle(
            fontSize: 12,
            color: colorScheme.onSurface.withValues(alpha: 0.65),
          ),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 16),

        TextField(
          controller: _newPinController,
          keyboardType: TextInputType.number,
          obscureText: _obscureNewPin,
          maxLength: 6,
          decoration: InputDecoration(
            labelText: 'New PIN (4-6 digits)',
            prefixIcon: const Icon(Icons.pin),
            suffixIcon: IconButton(
              icon: Icon(
                _obscureNewPin ? Icons.visibility_off : Icons.visibility,
                semanticLabel: _obscureNewPin ? 'Show PIN' : 'Hide PIN',
              ),
              onPressed: () {
                setState(() => _obscureNewPin = !_obscureNewPin);
              },
            ),
            border: const OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 12),

        TextField(
          controller: _confirmPinController,
          keyboardType: TextInputType.number,
          obscureText: _obscureConfirmPin,
          maxLength: 6,
          decoration: InputDecoration(
            labelText: 'Confirm PIN',
            prefixIcon: const Icon(Icons.check_circle_outline),
            suffixIcon: IconButton(
              icon: Icon(
                _obscureConfirmPin ? Icons.visibility_off : Icons.visibility,
                semanticLabel: _obscureConfirmPin ? 'Show PIN' : 'Hide PIN',
              ),
              onPressed: () {
                setState(() => _obscureConfirmPin = !_obscureConfirmPin);
              },
            ),
            border: const OutlineInputBorder(),
          ),
          onSubmitted: (_) => _handleSetPin(),
        ),
        const SizedBox(height: 16),

        ElevatedButton(
          onPressed: _handleSetPin,
          style: ElevatedButton.styleFrom(
            backgroundColor: colorScheme.primary,
            foregroundColor: colorScheme.onPrimary,
            padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 12),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            mainAxisSize: MainAxisSize.min,
            children: const [
              Icon(Icons.save),
              SizedBox(width: 8),
              Flexible(
                child: Text(
                  'Save PIN & Enter App',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
