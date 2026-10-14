import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/auth_service.dart';
import '../services/theme_service.dart';

class ProfileScreen extends StatefulWidget {
  final VoidCallback? onOpenDrawer;

  const ProfileScreen({super.key, this.onOpenDrawer});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  final _authService = MobileAuthService.instance;

  Map<String, dynamic> _user = {};
  String _deviceId = '';
  bool _isLoading = true;
  bool _hasPin = false;

  @override
  void initState() {
    super.initState();
    _loadProfileData();
  }

  Future<void> _loadProfileData() async {
    setState(() => _isLoading = true);
    final user = await _authService.getCurrentUser();
    final deviceId = await _authService.getOrCreateDeviceId();
    final hasPin = await _authService.hasUserPin(user['email'] as String?);

    if (mounted) {
      setState(() {
        _user = user;
        _deviceId = deviceId;
        _hasPin = hasPin;
        _isLoading = false;
      });
    }
  }

  String _getInitials(String name) {
    if (name.trim().isEmpty) return 'CW';
    final parts = name.trim().split(RegExp(r'\s+'));
    if (parts.length >= 2) {
      return '${parts[0][0]}${parts[1][0]}'.toUpperCase();
    }
    return parts[0].substring(0, parts[0].length >= 2 ? 2 : 1).toUpperCase();
  }

  void _showCreatePinDialog() {
    final pinCtrl = TextEditingController();
    final confirmCtrl = TextEditingController();
    String? errorText;

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDlgState) => AlertDialog(
          title: const Text('Create Quick Access PIN'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text(
                'Enter a personal 4 to 6-digit numeric PIN for unlocking in the field.',
                style: TextStyle(fontSize: 13),
              ),
              const SizedBox(height: 16),
              if (errorText != null) ...[
                Text(errorText!, style: const TextStyle(color: Colors.red, fontSize: 12)),
                const SizedBox(height: 10),
              ],
              TextField(
                controller: pinCtrl,
                keyboardType: TextInputType.number,
                maxLength: 6,
                obscureText: true,
                decoration: const InputDecoration(labelText: 'New PIN (4-6 digits)', border: OutlineInputBorder()),
              ),
              const SizedBox(height: 8),
              TextField(
                controller: confirmCtrl,
                keyboardType: TextInputType.number,
                maxLength: 6,
                obscureText: true,
                decoration: const InputDecoration(labelText: 'Confirm PIN', border: OutlineInputBorder()),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              onPressed: () async {
                final p = pinCtrl.text.trim();
                final c = confirmCtrl.text.trim();
                if (p.length < 4 || p.length > 6) {
                  setDlgState(() => errorText = 'PIN must be 4 to 6 numeric digits.');
                  return;
                }
                if (p != c) {
                  setDlgState(() => errorText = 'PINs do not match.');
                  return;
                }
                final ok = await _authService.setPin(p, email: _user['email'] as String?);
                if (ok) {
                  if (ctx.mounted) Navigator.pop(ctx);
                  setState(() => _hasPin = true);
                  if (mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Quick Access PIN created successfully.')),
                    );
                  }
                } else {
                  setDlgState(() => errorText = 'Failed to derive PBKDF2 hash.');
                }
              },
              child: const Text('Save PIN'),
            ),
          ],
        ),
      ),
    );
  }

  void _showChangePinDialog() {
    final currentPinCtrl = TextEditingController();
    final newPinCtrl = TextEditingController();
    final confirmCtrl = TextEditingController();
    String? errorText;

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDlgState) => AlertDialog(
          title: const Text('Change Quick Access PIN'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              if (errorText != null) ...[
                Text(errorText!, style: const TextStyle(color: Colors.red, fontSize: 12)),
                const SizedBox(height: 10),
              ],
              TextField(
                controller: currentPinCtrl,
                keyboardType: TextInputType.number,
                maxLength: 6,
                obscureText: true,
                decoration: const InputDecoration(labelText: 'Current PIN', border: OutlineInputBorder()),
              ),
              const SizedBox(height: 8),
              TextField(
                controller: newPinCtrl,
                keyboardType: TextInputType.number,
                maxLength: 6,
                obscureText: true,
                decoration: const InputDecoration(labelText: 'New PIN (4-6 digits)', border: OutlineInputBorder()),
              ),
              const SizedBox(height: 8),
              TextField(
                controller: confirmCtrl,
                keyboardType: TextInputType.number,
                maxLength: 6,
                obscureText: true,
                decoration: const InputDecoration(labelText: 'Confirm New PIN', border: OutlineInputBorder()),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              onPressed: () async {
                final cur = currentPinCtrl.text.trim();
                final p = newPinCtrl.text.trim();
                final c = confirmCtrl.text.trim();

                final verifyRes = await _authService.unlockWithPin(cur, email: _user['email'] as String?);
                if (!verifyRes.success) {
                  setDlgState(() => errorText = verifyRes.errorMessage ?? 'Current PIN is incorrect.');
                  return;
                }

                if (p.length < 4 || p.length > 6) {
                  setDlgState(() => errorText = 'New PIN must be 4 to 6 numeric digits.');
                  return;
                }
                if (p != c) {
                  setDlgState(() => errorText = 'New PINs do not match.');
                  return;
                }

                final ok = await _authService.setPin(p, email: _user['email'] as String?);
                if (ok) {
                  if (ctx.mounted) Navigator.pop(ctx);
                  setState(() => _hasPin = true);
                  if (mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Quick Access PIN updated successfully.')),
                    );
                  }
                } else {
                  setDlgState(() => errorText = 'Failed to update PIN.');
                }
              },
              child: const Text('Update PIN'),
            ),
          ],
        ),
      ),
    );
  }

  void _showResetPinWithPasswordDialog() {
    final passwordCtrl = TextEditingController();
    final newPinCtrl = TextEditingController();
    final confirmCtrl = TextEditingController();
    bool obscurePassword = true;
    bool isSubmitting = false;
    String? errorText;

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDlgState) => AlertDialog(
          title: const Text('Reset PIN with Password'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text(
                  'Verify your CRBCL account password to set a new Quick Access PIN.',
                  style: TextStyle(fontSize: 13),
                ),
                const SizedBox(height: 16),
                if (errorText != null) ...[
                  Text(errorText!, style: const TextStyle(color: Colors.red, fontSize: 12)),
                  const SizedBox(height: 10),
                ],
                TextField(
                  controller: passwordCtrl,
                  obscureText: obscurePassword,
                  decoration: InputDecoration(
                    labelText: 'CRBCL Account Password',
                    border: const OutlineInputBorder(),
                    suffixIcon: IconButton(
                      icon: Icon(obscurePassword ? Icons.visibility_off : Icons.visibility),
                      onPressed: () => setDlgState(() => obscurePassword = !obscurePassword),
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: newPinCtrl,
                  keyboardType: TextInputType.number,
                  maxLength: 6,
                  obscureText: true,
                  decoration: const InputDecoration(labelText: 'New PIN (4-6 digits)', border: OutlineInputBorder()),
                ),
                const SizedBox(height: 8),
                TextField(
                  controller: confirmCtrl,
                  keyboardType: TextInputType.number,
                  maxLength: 6,
                  obscureText: true,
                  decoration: const InputDecoration(labelText: 'Confirm New PIN', border: OutlineInputBorder()),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              onPressed: isSubmitting
                  ? null
                  : () async {
                      final pwd = passwordCtrl.text;
                      final p = newPinCtrl.text.trim();
                      final c = confirmCtrl.text.trim();

                      if (pwd.isEmpty) {
                        setDlgState(() => errorText = 'Please enter your account password.');
                        return;
                      }
                      if (p.length < 4 || p.length > 6) {
                        setDlgState(() => errorText = 'New PIN must be 4 to 6 numeric digits.');
                        return;
                      }
                      if (p != c) {
                        setDlgState(() => errorText = 'PINs do not match.');
                        return;
                      }

                      setDlgState(() {
                        isSubmitting = true;
                        errorText = null;
                      });

                      final res = await _authService.verifyPasswordAndResetPin(
                        password: pwd,
                        newPin: p,
                        email: _user['email'] as String?,
                      );

                      setDlgState(() => isSubmitting = false);

                      if (res['success'] == true) {
                        if (ctx.mounted) Navigator.pop(ctx);
                        setState(() => _hasPin = true);
                        if (mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(content: Text(res['message'] as String? ?? 'PIN reset successfully!')),
                          );
                        }
                      } else {
                        setDlgState(() => errorText = res['errorMessage'] as String? ?? 'Password verification failed.');
                      }
                    },
              child: isSubmitting
                  ? const SizedBox(height: 16, width: 16, child: CircularProgressIndicator(strokeWidth: 2))
                  : const Text('Reset & Save PIN'),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;
    final isDark = theme.brightness == Brightness.dark;
    final themeService = Provider.of<MobileThemeService>(context);

    final displayName = (_user['name'] as String?)?.isNotEmpty == true
        ? _user['name'] as String
        : 'CRBCL Caseworker';
    final email = (_user['email'] as String?)?.isNotEmpty == true
        ? _user['email'] as String
        : 'Not provided';

    return Scaffold(
      appBar: AppBar(
        leading: widget.onOpenDrawer != null
            ? IconButton(
                icon: const Icon(Icons.menu),
                tooltip: 'Open navigation menu',
                onPressed: widget.onOpenDrawer,
              )
            : null,
        title: const Text('Profile & Settings'),
        actions: [
          IconButton(
            icon: const Icon(Icons.lock_outline),
            tooltip: 'Lock Vault',
            onPressed: () => Navigator.pushReplacementNamed(context, '/login'),
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // User Profile Header Card
                  Card(
                    elevation: isDark ? 0 : 2,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(14),
                      side: BorderSide(
                        color: isDark ? colorScheme.outlineVariant : CrbclTokens.lightBorder,
                        width: 1,
                      ),
                    ),
                    color: colorScheme.surfaceContainer,
                    child: Padding(
                      padding: const EdgeInsets.all(20.0),
                      child: Column(
                        children: [
                          CircleAvatar(
                            radius: 36,
                            backgroundColor: colorScheme.primary.withValues(alpha: 0.15),
                            child: Text(
                              _getInitials(displayName),
                              style: TextStyle(
                                fontSize: 24,
                                fontWeight: FontWeight.bold,
                                color: colorScheme.primary,
                              ),
                            ),
                          ),
                          const SizedBox(height: 12),
                          Text(
                            displayName,
                            style: TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                              color: colorScheme.onSurface,
                            ),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            email,
                            style: TextStyle(
                              fontSize: 13,
                              color: colorScheme.onSurface.withValues(alpha: 0.65),
                            ),
                          ),
                          const SizedBox(height: 10),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                            decoration: BoxDecoration(
                              color: colorScheme.onSurface.withValues(alpha: 0.08),
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Text(
                              'Cote First Nation',
                              style: TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.w600,
                                color: colorScheme.onSurface.withValues(alpha: 0.7),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 20),

                  // Quick Access PIN Management Card
                  Text(
                    'Quick Access PIN Security',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: colorScheme.onSurface,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Personalized offline biometric/PIN unlocking for your account on this device.',
                    style: TextStyle(
                      fontSize: 12,
                      color: colorScheme.onSurface.withValues(alpha: 0.6),
                    ),
                  ),
                  const SizedBox(height: 10),

                  Card(
                    elevation: 0,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                      side: BorderSide(
                        color: isDark ? colorScheme.outlineVariant : CrbclTokens.lightBorder,
                      ),
                    ),
                    color: colorScheme.surfaceContainer,
                    child: Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          Row(
                            children: [
                              CircleAvatar(
                                radius: 18,
                                backgroundColor: _hasPin
                                    ? CrbclTokens.statusSuccess.withValues(alpha: 0.15)
                                    : Colors.amber.withValues(alpha: 0.15),
                                child: Icon(
                                  _hasPin ? Icons.pin : Icons.pin_outlined,
                                  size: 20,
                                  color: _hasPin ? CrbclTokens.statusSuccess : Colors.amber.shade800,
                                ),
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      _hasPin ? 'Quick Access PIN Active' : 'No PIN Configured',
                                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                                    ),
                                    Text(
                                      _hasPin
                                          ? 'PBKDF2 HMAC-SHA256 • 100k rounds'
                                          : 'Set a PIN for quick offline unlocking in the field',
                                      style: TextStyle(
                                        fontSize: 11,
                                        color: colorScheme.onSurface.withValues(alpha: 0.65),
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                decoration: BoxDecoration(
                                  color: _hasPin
                                      ? CrbclTokens.statusSuccess.withValues(alpha: 0.12)
                                      : Colors.amber.withValues(alpha: 0.15),
                                  borderRadius: BorderRadius.circular(10),
                                ),
                                child: Text(
                                  _hasPin ? 'PROTECTED' : 'UNSET',
                                  style: TextStyle(
                                    fontSize: 10,
                                    fontWeight: FontWeight.bold,
                                    color: _hasPin ? CrbclTokens.statusSuccess : Colors.amber.shade900,
                                  ),
                                ),
                              ),
                            ],
                          ),
                          const Divider(height: 24),

                          // PIN Action Buttons
                          Wrap(
                            spacing: 8,
                            runSpacing: 8,
                            children: [
                              if (!_hasPin)
                                ElevatedButton.icon(
                                  onPressed: _showCreatePinDialog,
                                  icon: const Icon(Icons.add, size: 16),
                                  label: const Text('Create Quick PIN'),
                                  style: ElevatedButton.styleFrom(
                                    backgroundColor: colorScheme.primary,
                                    foregroundColor: colorScheme.onPrimary,
                                  ),
                                )
                              else ...[
                                OutlinedButton.icon(
                                  onPressed: _showChangePinDialog,
                                  icon: const Icon(Icons.lock_reset, size: 16),
                                  label: const Text('Change PIN'),
                                ),
                                TextButton.icon(
                                  onPressed: _showResetPinWithPasswordDialog,
                                  icon: const Icon(Icons.password, size: 16),
                                  label: const Text('Forgot PIN? Reset with Password'),
                                ),
                              ],
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 20),

                  // Appearance & Personalization Section
                  Text(
                    'Appearance & Personalization',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: colorScheme.onSurface,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Personalize theme and accessibility while preserving official CRBCL branding.',
                    style: TextStyle(
                      fontSize: 12,
                      color: colorScheme.onSurface.withValues(alpha: 0.6),
                    ),
                  ),
                  const SizedBox(height: 12),

                  // Theme Mode Selector
                  SegmentedButton<ThemeMode>(
                    segments: const [
                      ButtonSegment(value: ThemeMode.light, icon: Icon(Icons.light_mode), label: Text('Light')),
                      ButtonSegment(value: ThemeMode.dark, icon: Icon(Icons.dark_mode), label: Text('Dark')),
                      ButtonSegment(value: ThemeMode.system, icon: Icon(Icons.settings_suggest), label: Text('System')),
                    ],
                    selected: {themeService.themeMode},
                    onSelectionChanged: (Set<ThemeMode> newSelection) {
                      themeService.updatePreferences(mode: newSelection.first);
                    },
                  ),
                  const SizedBox(height: 16),

                  // Accent Palette Swatches
                  Text(
                    'Lodge Accent Palette',
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                      color: colorScheme.onSurface,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: MobileThemeService.palettes.map((palette) {
                      final isSelected = themeService.accentKey == palette.key;
                      return ChoiceChip(
                        label: Text(
                          palette.label,
                          style: TextStyle(
                            fontSize: 11,
                            color: isSelected ? colorScheme.primary : colorScheme.onSurface,
                          ),
                        ),
                        avatar: CircleAvatar(backgroundColor: palette.primary, radius: 7),
                        selected: isSelected,
                        onSelected: (selected) {
                          if (selected) {
                            themeService.updatePreferences(accent: palette.key);
                          }
                        },
                      );
                    }).toList(),
                  ),
                  const SizedBox(height: 16),

                  // Density & Contrast Switches
                  SwitchListTile(
                    title: const Text('Compact Layout Density', style: TextStyle(fontSize: 14)),
                    subtitle: const Text('Tighter cards and list spacing', style: TextStyle(fontSize: 11)),
                    value: themeService.density == 'compact',
                    onChanged: (val) {
                      themeService.updatePreferences(density: val ? 'compact' : 'comfortable');
                    },
                  ),
                  SwitchListTile(
                    title: const Text('High-Contrast Accessibility', style: TextStyle(fontSize: 14)),
                    subtitle: const Text('Stronger card outlines and borders', style: TextStyle(fontSize: 11)),
                    value: themeService.highContrast,
                    onChanged: (val) {
                      themeService.updatePreferences(highContrast: val);
                    },
                  ),
                  const SizedBox(height: 10),

                  // Reset Appearance
                  OutlinedButton.icon(
                    onPressed: () {
                      themeService.updatePreferences(
                        mode: ThemeMode.system,
                        accent: 'crbcl',
                        density: 'comfortable',
                        highContrast: false,
                        reducedMotion: false,
                      );
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('Appearance restored to CRBCL Default')),
                      );
                    },
                    icon: const Icon(Icons.refresh),
                    label: const Text('Reset Appearance to CRBCL Default'),
                  ),
                  const SizedBox(height: 24),

                  // Security & Storage Section
                  const Divider(),
                  const SizedBox(height: 12),
                  Text(
                    'Device & Offline Security',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: colorScheme.onSurface,
                    ),
                  ),
                  const SizedBox(height: 12),

                  Card(
                    elevation: 0,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(10),
                      side: BorderSide(
                        color: isDark ? colorScheme.outlineVariant : CrbclTokens.lightBorder,
                      ),
                    ),
                    color: colorScheme.surfaceContainer,
                    child: Padding(
                      padding: const EdgeInsets.all(14.0),
                      child: Column(
                        children: [
                          Row(
                            children: [
                              const Icon(Icons.security, size: 20, color: CrbclTokens.statusSuccess),
                              const SizedBox(width: 10),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      'Offline Vault Encryption',
                                      style: TextStyle(
                                        fontWeight: FontWeight.bold,
                                        fontSize: 13,
                                        color: colorScheme.onSurface,
                                      ),
                                    ),
                                    Text(
                                      'AES-256 SQLCipher Active',
                                      style: TextStyle(
                                        fontSize: 11,
                                        color: colorScheme.onSurface.withValues(alpha: 0.65),
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                              const Icon(Icons.check_circle, size: 18, color: CrbclTokens.statusSuccess),
                            ],
                          ),
                          const Divider(height: 20),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text(
                                'Device ID',
                                style: TextStyle(
                                  fontSize: 12,
                                  color: colorScheme.onSurface.withValues(alpha: 0.65),
                                ),
                              ),
                              Text(
                                _deviceId.isNotEmpty ? _deviceId : 'DEV-MOBILE-UNIT',
                                style: TextStyle(
                                  fontSize: 12,
                                  fontWeight: FontWeight.bold,
                                  fontFamily: 'monospace',
                                  color: colorScheme.onSurface,
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),

                  // Switch Account Button
                  OutlinedButton.icon(
                    onPressed: () async {
                      await _authService.switchUser();
                      if (context.mounted) {
                        Navigator.pushReplacementNamed(context, '/login');
                      }
                    },
                    icon: const Icon(Icons.swap_horiz),
                    label: const Text('Switch Account / Sign In as Different User'),
                    style: OutlinedButton.styleFrom(
                      minimumSize: const Size.fromHeight(46),
                    ),
                  ),
                  const SizedBox(height: 10),

                  // Lock Vault Button
                  ElevatedButton.icon(
                    onPressed: () {
                      Navigator.pushReplacementNamed(context, '/login');
                    },
                    icon: const Icon(Icons.lock_outline),
                    label: const Text('Lock Vault & Sign Out'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: colorScheme.error,
                      foregroundColor: Colors.white,
                      minimumSize: const Size.fromHeight(48),
                    ),
                  ),
                ],
              ),
            ),
    );
  }
}
