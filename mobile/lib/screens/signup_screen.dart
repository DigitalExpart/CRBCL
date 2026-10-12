import 'package:flutter/material.dart';
import '../services/auth_service.dart';
import '../services/theme_service.dart';
import '../widgets/crbcl_logo.dart';

class SignUpScreen extends StatefulWidget {
  const SignUpScreen({super.key});

  @override
  State<SignUpScreen> createState() => _SignUpScreenState();
}

class _SignUpScreenState extends State<SignUpScreen> {
  final _authService = MobileAuthService.instance;

  final _fullNameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  final _departmentController = TextEditingController();
  final _otpController = TextEditingController();

  String _selectedRole = 'caseworker';
  bool _obscurePassword = true;
  bool _obscureConfirmPassword = true;
  bool _isLoading = false;
  String? _errorMessage;
  String? _successMessage;

  // Step 2: OTP verification state
  bool _isAwaitingOtp = false;
  String _pendingEmail = '';

  final List<Map<String, String>> _availableRoles = const [
    {'key': 'caseworker', 'label': 'Caseworker'},
    {'key': 'supervisor', 'label': 'Supervisor'},
    {'key': 'cultural_worker', 'label': 'Cultural Worker'},
    {'key': 'case_aide', 'label': 'Case Aide'},
    {'key': 'clinical_staff', 'label': 'Clinical Staff'},
    {'key': 'resource_worker', 'label': 'Resource Worker'},
    {'key': 'front_desk', 'label': 'Front Desk'},
    {'key': 'navigator', 'label': 'Navigator'},
    {'key': 'it_admin', 'label': 'IT Administrator'},
    {'key': 'executive_director', 'label': 'Executive Director'},
  ];

  @override
  void dispose() {
    _fullNameController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    _departmentController.dispose();
    _otpController.dispose();
    super.dispose();
  }

  Future<void> _handleRegister() async {
    final fullName = _fullNameController.text.trim();
    final email = _emailController.text.trim();
    final password = _passwordController.text;
    final confirmPassword = _confirmPasswordController.text;
    final department = _departmentController.text.trim();

    if (fullName.isEmpty || email.isEmpty || password.isEmpty) {
      setState(() => _errorMessage = 'Please complete all required fields.');
      return;
    }

    if (!email.contains('@') || !email.contains('.')) {
      setState(() => _errorMessage = 'Please enter a valid email address.');
      return;
    }

    if (password.length < 8) {
      setState(() => _errorMessage = 'Password must be at least 8 characters long.');
      return;
    }

    if (password != confirmPassword) {
      setState(() => _errorMessage = 'Passwords do not match. Please re-enter.');
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
      _successMessage = null;
    });

    final res = await _authService.registerOnline(
      email: email,
      password: password,
      fullName: fullName,
      requestedRole: _selectedRole,
      department: department.isNotEmpty ? department : 'Family Wellness',
    );

    setState(() => _isLoading = false);

    if (res['success'] == true) {
      setState(() {
        _isAwaitingOtp = true;
        _pendingEmail = email;
        _successMessage = res['message'] as String?;
      });
    } else {
      setState(() {
        _errorMessage = res['errorMessage'] as String? ?? 'Registration failed.';
      });
    }
  }

  Future<void> _handleVerifyOtp() async {
    final otpCode = _otpController.text.trim();
    if (otpCode.length < 4) {
      setState(() => _errorMessage = 'Please enter the verification code.');
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final res = await _authService.verifyOtpOnline(
      email: _pendingEmail,
      otpCode: otpCode,
    );

    setState(() => _isLoading = false);

    if (res.success) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Account verified! Please set up your Quick PIN.')),
        );
        Navigator.pushReplacementNamed(context, '/login');
      }
    } else {
      setState(() {
        _errorMessage = res.errorMessage ?? 'Verification failed.';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;
    final isDark = theme.brightness == Brightness.dark;

    return Scaffold(
      backgroundColor: theme.scaffoldBackgroundColor,
      appBar: AppBar(
        title: const Text('Staff Registration'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 16.0),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 440),
              child: Card(
                elevation: isDark ? 0 : 2,
                color: colorScheme.surfaceContainer,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                  side: BorderSide(
                    color: isDark ? colorScheme.outlineVariant : CrbclTokens.lightBorder,
                    width: 1,
                  ),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(24.0),
                  child: _isAwaitingOtp ? _buildOtpView() : _buildRegistrationForm(),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildRegistrationForm() {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      mainAxisSize: MainAxisSize.min,
      children: [
        const Center(
          child: CrbclLogo(height: 52, variant: CrbclLogoVariant.emblem),
        ),
        const SizedBox(height: 12),
        Text(
          'Join CRBCL Staff',
          style: TextStyle(
            fontFamily: CrbclTokens.fontHeading,
            fontSize: 22,
            fontWeight: FontWeight.bold,
            color: colorScheme.onSurface,
          ),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 4),
        Text(
          'Create your mobile field operations account',
          style: TextStyle(
            fontSize: 13,
            color: colorScheme.onSurface.withValues(alpha: 0.7),
          ),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 20),

        if (_errorMessage != null) ...[
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.red.shade50.withValues(alpha: 0.9),
              border: Border.all(color: Colors.red.shade200),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(Icons.error_outline, color: Colors.red.shade800, size: 20),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    _errorMessage!,
                    style: TextStyle(color: Colors.red.shade900, fontSize: 13),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
        ],

        // Full Name
        TextField(
          controller: _fullNameController,
          decoration: const InputDecoration(
            labelText: 'Full Name *',
            hintText: 'e.g. Jane Bear',
            prefixIcon: Icon(Icons.person_outline),
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 12),

        // Email
        TextField(
          controller: _emailController,
          keyboardType: TextInputType.emailAddress,
          decoration: const InputDecoration(
            labelText: 'Work Email *',
            hintText: 'name@crbcl.ca',
            prefixIcon: Icon(Icons.email_outlined),
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 12),

        // Role Dropdown
        DropdownButtonFormField<String>(
          initialValue: _selectedRole,
          decoration: const InputDecoration(
            labelText: 'Platform Role *',
            prefixIcon: Icon(Icons.badge_outlined),
            border: OutlineInputBorder(),
          ),
          items: _availableRoles.map((r) {
            return DropdownMenuItem<String>(
              value: r['key'],
              child: Text(r['label']!),
            );
          }).toList(),
          onChanged: (val) {
            if (val != null) setState(() => _selectedRole = val);
          },
        ),
        const SizedBox(height: 12),

        // Department
        TextField(
          controller: _departmentController,
          decoration: const InputDecoration(
            labelText: 'Department (Optional)',
            hintText: 'Family Wellness',
            prefixIcon: Icon(Icons.business_outlined),
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 12),

        // Password
        TextField(
          controller: _passwordController,
          obscureText: _obscurePassword,
          decoration: InputDecoration(
            labelText: 'Password (min. 8 characters) *',
            prefixIcon: const Icon(Icons.lock_outline),
            suffixIcon: IconButton(
              icon: Icon(_obscurePassword ? Icons.visibility_off : Icons.visibility),
              onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
            ),
            border: const OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 12),

        // Confirm Password
        TextField(
          controller: _confirmPasswordController,
          obscureText: _obscureConfirmPassword,
          decoration: InputDecoration(
            labelText: 'Confirm Password *',
            prefixIcon: const Icon(Icons.lock_outline),
            suffixIcon: IconButton(
              icon: Icon(_obscureConfirmPassword ? Icons.visibility_off : Icons.visibility),
              onPressed: () => setState(() => _obscureConfirmPassword = !_obscureConfirmPassword),
            ),
            border: const OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 20),

        // Submit Button
        ElevatedButton(
          onPressed: _isLoading ? null : _handleRegister,
          style: ElevatedButton.styleFrom(
            backgroundColor: colorScheme.primary,
            foregroundColor: colorScheme.onPrimary,
            padding: const EdgeInsets.symmetric(vertical: 14),
          ),
          child: _isLoading
              ? const SizedBox(
                  height: 20,
                  width: 20,
                  child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                )
              : const Text('Create Account', style: TextStyle(fontWeight: FontWeight.bold)),
        ),
        const SizedBox(height: 16),

        // Back to login
        Wrap(
          alignment: WrapAlignment.center,
          crossAxisAlignment: WrapCrossAlignment.center,
          children: [
            Text(
              'Already have an account? ',
              style: TextStyle(fontSize: 13, color: colorScheme.onSurface.withValues(alpha: 0.7)),
            ),
            GestureDetector(
              onTap: () => Navigator.pop(context),
              child: Text(
                'Sign In',
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.bold,
                  color: colorScheme.primary,
                ),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildOtpView() {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      mainAxisSize: MainAxisSize.min,
      children: [
        const Center(
          child: Icon(Icons.mark_email_read_outlined, size: 54, color: Colors.green),
        ),
        const SizedBox(height: 12),
        Text(
          'Verify Your Email',
          style: TextStyle(
            fontFamily: CrbclTokens.fontHeading,
            fontSize: 20,
            fontWeight: FontWeight.bold,
            color: colorScheme.onSurface,
          ),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 6),
        Text(
          'A 6-digit verification code was sent to:\n$_pendingEmail',
          style: TextStyle(
            fontSize: 13,
            color: colorScheme.onSurface.withValues(alpha: 0.7),
          ),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 20),

        if (_successMessage != null) ...[
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.green.shade50.withValues(alpha: 0.9),
              border: Border.all(color: Colors.green.shade200),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(Icons.check_circle_outline, color: Colors.green.shade800, size: 20),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    _successMessage!,
                    style: TextStyle(color: Colors.green.shade900, fontSize: 13),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
        ],

        if (_errorMessage != null) ...[
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.red.shade50.withValues(alpha: 0.9),
              border: Border.all(color: Colors.red.shade200),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(Icons.error_outline, color: Colors.red.shade800, size: 20),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    _errorMessage!,
                    style: TextStyle(color: Colors.red.shade900, fontSize: 13),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
        ],

        TextField(
          controller: _otpController,
          keyboardType: TextInputType.number,
          textAlign: TextAlign.center,
          style: const TextStyle(fontSize: 22, letterSpacing: 8, fontWeight: FontWeight.bold),
          decoration: const InputDecoration(
            labelText: 'Enter 6-Digit Code',
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 16),

        ElevatedButton(
          onPressed: _isLoading ? null : _handleVerifyOtp,
          style: ElevatedButton.styleFrom(
            backgroundColor: colorScheme.primary,
            foregroundColor: colorScheme.onPrimary,
            padding: const EdgeInsets.symmetric(vertical: 14),
          ),
          child: _isLoading
              ? const SizedBox(
                  height: 20,
                  width: 20,
                  child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                )
              : const Text('Verify & Register Device', style: TextStyle(fontWeight: FontWeight.bold)),
        ),
        const SizedBox(height: 12),

        TextButton(
          onPressed: () {
            setState(() {
              _isAwaitingOtp = false;
              _errorMessage = null;
            });
          },
          child: const Text('Back to Sign-Up Details'),
        ),
      ],
    );
  }
}
