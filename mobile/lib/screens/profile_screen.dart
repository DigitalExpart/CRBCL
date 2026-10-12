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

  @override
  void initState() {
    super.initState();
    _loadProfileData();
  }

  Future<void> _loadProfileData() async {
    setState(() => _isLoading = true);
    final user = await _authService.getCurrentUser();
    final deviceId = await _authService.getOrCreateDeviceId();

    if (mounted) {
      setState(() {
        _user = user;
        _deviceId = deviceId;
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
    final roles = (_user['roles'] as List?)?.cast<String>() ?? [];
    final roleLabel = roles.isNotEmpty ? roles.join(', ') : 'Field Staff';

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
                          Wrap(
                            alignment: WrapAlignment.center,
                            spacing: 6,
                            runSpacing: 4,
                            children: [
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
                                decoration: BoxDecoration(
                                  color: colorScheme.primary.withValues(alpha: 0.12),
                                  borderRadius: BorderRadius.circular(12),
                                ),
                                child: Text(
                                  roleLabel,
                                  style: TextStyle(
                                    fontSize: 11,
                                    fontWeight: FontWeight.bold,
                                    color: colorScheme.primary,
                                  ),
                                ),
                              ),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
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
                  const SizedBox(height: 12),

                  // Notice regarding credentials
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: colorScheme.primary.withValues(alpha: 0.08),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      'Account credentials, RBAC permissions, and passwords are managed through the central CRBCL web platform.',
                      style: TextStyle(
                        fontSize: 11,
                        color: colorScheme.onSurface.withValues(alpha: 0.7),
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ),
                  const SizedBox(height: 16),

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
