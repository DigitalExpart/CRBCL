import 'package:flutter/material.dart';
import '../services/auth_service.dart';
import '../services/theme_service.dart';
import '../widgets/crbcl_logo.dart';

class AdminLoginScreen extends StatefulWidget {
  const AdminLoginScreen({super.key});

  @override
  State<AdminLoginScreen> createState() => _AdminLoginScreenState();
}

class _AdminLoginScreenState extends State<AdminLoginScreen> {
  final _emailController = TextEditingController(text: 'admin@crbcl.ca');
  final _passwordController = TextEditingController();
  final _pinController = TextEditingController();
  final _authService = MobileAuthService.instance;

  bool _obscurePassword = true;
  bool _obscurePin = true;
  bool _isLoading = false;
  bool _hasAdminPin = false;
  bool _isPinMode = false;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _checkAdminPin();
  }

  Future<void> _checkAdminPin() async {
    final hasPin = await _authService.hasAdminPin();
    if (mounted) {
      setState(() {
        _hasAdminPin = hasPin;
        _isPinMode = hasPin;
      });
    }
  }

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    _pinController.dispose();
    super.dispose();
  }

  Future<void> _handleAdminPinUnlock() async {
    final pin = _pinController.text.trim();
    if (pin.length < 4 || pin.length > 6) {
      setState(() => _errorMessage = 'Please enter a valid 4 or 6-digit PIN.');
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final result = await _authService.unlockWithPin(pin, email: 'admin@crbcl.ca');
    setState(() => _isLoading = false);

    if (result.success) {
      if (mounted) {
        Navigator.pushReplacementNamed(context, '/admin-dashboard');
      }
    } else {
      setState(() => _errorMessage = result.errorMessage);
    }
  }

  Future<void> _handleAdminLogin() async {
    final email = _emailController.text.trim();
    final password = _passwordController.text;

    if (email.isEmpty || password.isEmpty) {
      setState(() => _errorMessage = 'Please enter administrator email and password.');
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final result = await _authService.loginAdminOnline(
      email: email,
      password: password,
    );

    setState(() => _isLoading = false);

    if (!result.success) {
      setState(() => _errorMessage = result.errorMessage ?? 'Administrator authentication failed.');
      return;
    }

    if (mounted) {
      Navigator.pushReplacementNamed(context, '/admin-dashboard');
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    // Distinct IT Admin styling tokens matching web /admin portal
    const adminPurple = Color(0xFF6B21A8);
    const adminPurpleLight = Color(0xFF7E22CE);

    return Scaffold(
      backgroundColor: isDark ? const Color(0xFF140F18) : const Color(0xFFF9F7FA),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          tooltip: 'Return to Staff Login',
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 12.0),
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
                          height: 64,
                          variant: CrbclLogoVariant.emblem,
                        ),
                        const SizedBox(height: 12),
                        const Text(
                          'Chief Red Bear',
                          style: TextStyle(
                            fontFamily: CrbclTokens.fontHeading,
                            fontSize: 20,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          "Children's Lodge",
                          style: TextStyle(
                            fontSize: 13,
                            color: theme.colorScheme.onSurface.withValues(alpha: 0.65),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 20),

                  // Admin Card
                  Card(
                    elevation: isDark ? 0 : 3,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16),
                      side: BorderSide(
                        color: isDark ? adminPurple.withValues(alpha: 0.4) : const Color(0xFFE9D5FF),
                        width: 1.5,
                      ),
                    ),
                    color: isDark ? const Color(0xFF1F1726) : Colors.white,
                    child: Padding(
                      padding: const EdgeInsets.all(24.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          // Shield Header
                          Center(
                            child: Container(
                              padding: const EdgeInsets.all(12),
                              decoration: BoxDecoration(
                                color: adminPurple.withValues(alpha: 0.12),
                                shape: BoxShape.circle,
                              ),
                              child: const Icon(
                                Icons.admin_panel_settings_rounded,
                                size: 36,
                                color: adminPurpleLight,
                              ),
                            ),
                          ),
                          const SizedBox(height: 12),
                          const Text(
                            'IT Admin Portal',
                            textAlign: TextAlign.center,
                            style: TextStyle(
                              fontSize: 20,
                              fontWeight: FontWeight.bold,
                              letterSpacing: 0.2,
                            ),
                          ),
                          const SizedBox(height: 6),
                          Text(
                            _isPinMode
                                ? 'Enter your administrator Quick Access PIN to unlock the console'
                                : 'Restricted sign-in exclusively for CRBCL IT Administrators',
                            textAlign: TextAlign.center,
                            style: TextStyle(
                              fontSize: 12,
                              color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
                            ),
                          ),
                          const SizedBox(height: 20),

                          if (_errorMessage != null) ...[
                            Container(
                              padding: const EdgeInsets.all(12),
                              decoration: BoxDecoration(
                                color: theme.colorScheme.error.withValues(alpha: 0.12),
                                border: Border.all(color: theme.colorScheme.error.withValues(alpha: 0.3)),
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: Row(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Icon(Icons.shield_outlined, size: 18, color: theme.colorScheme.error),
                                  const SizedBox(width: 8),
                                  Expanded(
                                    child: Text(
                                      _errorMessage!,
                                      style: TextStyle(fontSize: 13, color: theme.colorScheme.error),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            const SizedBox(height: 16),
                          ],

                          if (_isPinMode) ...[
                            // PIN Mode UI
                            Container(
                              padding: const EdgeInsets.all(12),
                              decoration: BoxDecoration(
                                color: adminPurple.withValues(alpha: 0.08),
                                borderRadius: BorderRadius.circular(10),
                              ),
                              child: Row(
                                children: [
                                  const CircleAvatar(
                                    radius: 18,
                                    backgroundColor: adminPurple,
                                    child: Text('AD', style: TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.bold)),
                                  ),
                                  const SizedBox(width: 12),
                                  Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      const Text('System Administrator', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                                      Text('admin@crbcl.ca', style: TextStyle(fontSize: 11, color: theme.colorScheme.onSurface.withValues(alpha: 0.6))),
                                    ],
                                  ),
                                ],
                              ),
                            ),
                            const SizedBox(height: 16),
                            TextField(
                              controller: _pinController,
                              keyboardType: TextInputType.number,
                              maxLength: 6,
                              obscureText: _obscurePin,
                              decoration: InputDecoration(
                                labelText: 'Enter 4 or 6-digit PIN',
                                prefixIcon: const Icon(Icons.pin_outlined),
                                border: const OutlineInputBorder(),
                                suffixIcon: IconButton(
                                  icon: Icon(_obscurePin ? Icons.visibility_off : Icons.visibility),
                                  onPressed: () => setState(() => _obscurePin = !_obscurePin),
                                ),
                              ),
                              onSubmitted: (_) => _handleAdminPinUnlock(),
                            ),
                            const SizedBox(height: 14),
                            ElevatedButton(
                              onPressed: _isLoading ? null : _handleAdminPinUnlock,
                              style: ElevatedButton.styleFrom(
                                backgroundColor: adminPurple,
                                foregroundColor: Colors.white,
                                padding: const EdgeInsets.symmetric(vertical: 14),
                              ),
                              child: _isLoading
                                  ? const SizedBox(
                                      height: 20,
                                      width: 20,
                                      child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                                    )
                                  : Row(
                                      mainAxisAlignment: MainAxisAlignment.center,
                                      children: const [
                                        Icon(Icons.lock_open, size: 18),
                                        SizedBox(width: 8),
                                        Text('Unlock IT Admin Console', style: TextStyle(fontWeight: FontWeight.bold)),
                                      ],
                                    ),
                            ),
                            const SizedBox(height: 10),
                            TextButton.icon(
                              onPressed: () => setState(() {
                                _isPinMode = false;
                                _errorMessage = null;
                              }),
                              icon: const Icon(Icons.password, size: 16),
                              label: const Text('Use Administrator Password Instead'),
                            ),
                          ] else ...[
                            // Password Mode UI
                            TextField(
                              controller: _emailController,
                              keyboardType: TextInputType.emailAddress,
                              decoration: const InputDecoration(
                                labelText: 'Administrator Work Email',
                                hintText: 'admin@crbcl.ca',
                                prefixIcon: Icon(Icons.mail_outline),
                                border: OutlineInputBorder(),
                              ),
                            ),
                            const SizedBox(height: 14),
                            TextField(
                              controller: _passwordController,
                              obscureText: _obscurePassword,
                              decoration: InputDecoration(
                                labelText: 'Administrator Password',
                                prefixIcon: const Icon(Icons.lock_outline),
                                suffixIcon: IconButton(
                                  icon: Icon(_obscurePassword ? Icons.visibility_off : Icons.visibility),
                                  onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
                                ),
                                border: const OutlineInputBorder(),
                              ),
                              onSubmitted: (_) => _handleAdminLogin(),
                            ),
                            const SizedBox(height: 8),
                            Align(
                              alignment: Alignment.centerRight,
                              child: TextButton(
                                onPressed: () => Navigator.pushNamed(context, '/forgot-password'),
                                style: TextButton.styleFrom(visualDensity: VisualDensity.compact),
                                child: const Text('Forgot password?'),
                              ),
                            ),
                            const SizedBox(height: 12),
                            ElevatedButton(
                              onPressed: _isLoading ? null : _handleAdminLogin,
                              style: ElevatedButton.styleFrom(
                                backgroundColor: adminPurple,
                                foregroundColor: Colors.white,
                                padding: const EdgeInsets.symmetric(vertical: 14),
                              ),
                              child: _isLoading
                                  ? const SizedBox(
                                      height: 20,
                                      width: 20,
                                      child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                                    )
                                  : Row(
                                      mainAxisAlignment: MainAxisAlignment.center,
                                      children: const [
                                        Icon(Icons.security, size: 18),
                                        SizedBox(width: 8),
                                        Text('Access Admin Portal', style: TextStyle(fontWeight: FontWeight.bold)),
                                      ],
                                    ),
                            ),
                            if (_hasAdminPin) ...[
                              const SizedBox(height: 10),
                              TextButton.icon(
                                onPressed: () => setState(() {
                                  _isPinMode = true;
                                  _errorMessage = null;
                                }),
                                icon: const Icon(Icons.pin, size: 16),
                                label: const Text('Unlock with Quick Access PIN'),
                              ),
                            ],
                          ],
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 20),

                  // Link back to standard staff portal
                  Center(
                    child: Column(
                      children: [
                        Text(
                          'Frontline caseworker or field staff?',
                          style: TextStyle(
                            fontSize: 12,
                            color: theme.colorScheme.onSurface.withValues(alpha: 0.65),
                          ),
                        ),
                        const SizedBox(height: 4),
                        GestureDetector(
                          onTap: () => Navigator.pop(context),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Text(
                                'Go to Standard Portal',
                                style: TextStyle(
                                  fontSize: 13,
                                  fontWeight: FontWeight.bold,
                                  color: theme.colorScheme.primary,
                                ),
                              ),
                              const SizedBox(width: 4),
                              Icon(Icons.arrow_forward, size: 14, color: theme.colorScheme.primary),
                            ],
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
}
