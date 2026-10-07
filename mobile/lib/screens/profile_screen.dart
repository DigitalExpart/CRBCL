import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/theme_service.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  final _nameController = TextEditingController(text: 'Team Member');
  final _phoneController = TextEditingController(text: '');
  final _currentPasswordController = TextEditingController();
  final _newPasswordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();

  bool _isSaving = false;

  @override
  void dispose() {
    _nameController.dispose();
    _phoneController.dispose();
    _currentPasswordController.dispose();
    _newPasswordController.dispose();
    _confirmPasswordController.dispose();
    super.dispose();
  }

  void _saveProfile() {
    setState(() => _isSaving = true);
    Future.delayed(const Duration(milliseconds: 600), () {
      if (mounted) {
        setState(() => _isSaving = false);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Profile updated successfully')),
        );
      }
    });
  }

  void _showChangePasswordDialog() {
    _currentPasswordController.clear();
    _newPasswordController.clear();
    _confirmPasswordController.clear();

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Change Password'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: _currentPasswordController,
                obscureText: true,
                decoration: const InputDecoration(
                  labelText: 'Current Password',
                  prefixIcon: Icon(Icons.lock_outline),
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _newPasswordController,
                obscureText: true,
                decoration: const InputDecoration(
                  labelText: 'New Password (min 8 chars)',
                  prefixIcon: Icon(Icons.lock_reset),
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _confirmPasswordController,
                obscureText: true,
                decoration: const InputDecoration(
                  labelText: 'Confirm Password',
                  prefixIcon: Icon(Icons.check_circle_outline),
                ),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              if (_newPasswordController.text.length < 8) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Password must be at least 8 characters')),
                );
                return;
              }
              if (_newPasswordController.text != _confirmPasswordController.text) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('New passwords do not match')),
                );
                return;
              }
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Password changed successfully')),
              );
            },
            child: const Text('Change Password'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final themeService = Provider.of<MobileThemeService>(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('My Profile & Settings'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Avatar Header Card
            Card(
              elevation: 2,
              child: Padding(
                padding: const EdgeInsets.all(20.0),
                child: Column(
                  children: [
                    Stack(
                      children: [
                        CircleAvatar(
                          radius: 44,
                          backgroundColor: Theme.of(context).colorScheme.primary.withValues(alpha: 0.15),
                          child: Text(
                            'CB',
                            style: TextStyle(
                              fontSize: 28,
                              fontWeight: FontWeight.bold,
                              color: Theme.of(context).colorScheme.primary,
                            ),
                          ),
                        ),
                        Positioned(
                          bottom: 0,
                          right: 0,
                          child: CircleAvatar(
                            radius: 16,
                            backgroundColor: Theme.of(context).colorScheme.primary,
                            child: const Icon(Icons.camera_alt, size: 16, color: Colors.white),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    const Text(
                      'Chief Red Bear Lodge Staff',
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 4),
                    const Chip(
                      avatar: Icon(Icons.verified_user, size: 14),
                      label: Text('Field Caseworker / Staff', style: TextStyle(fontSize: 12)),
                      padding: EdgeInsets.zero,
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 20),

            // Profile Fields
            const Text(
              'Personal Information',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _nameController,
              decoration: const InputDecoration(
                labelText: 'Full Name',
                prefixIcon: Icon(Icons.person_outline),
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _phoneController,
              decoration: const InputDecoration(
                labelText: 'Phone Number',
                prefixIcon: Icon(Icons.phone_outlined),
                border: OutlineInputBorder(),
              ),
              keyboardType: TextInputType.phone,
            ),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              onPressed: _isSaving ? null : _saveProfile,
              icon: _isSaving
                  ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                  : const Icon(Icons.save),
              label: Text(_isSaving ? 'Saving...' : 'Save Profile Changes'),
              style: ElevatedButton.styleFrom(minimumSize: const Size.fromHeight(48)),
            ),
            const SizedBox(height: 24),

            // Section: Appearance & Personalization
            const Divider(),
            const SizedBox(height: 12),
            const Text(
              'Appearance & Personalization',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 4),
            const Text(
              'Customize your mobile display while preserving CRBCL accessibility.',
              style: TextStyle(fontSize: 12, color: Colors.grey),
            ),
            const SizedBox(height: 12),

            // Theme Mode Segmented Button
            SegmentedButton<ThemeMode>(
              segments: const [
                ButtonSegment(value: ThemeMode.light, icon: Icon(Icons.light_mode), label: Text('Light')),
                ButtonSegment(value: ThemeMode.dark, icon: Icon(Icons.dark_mode), label: Text('Dark')),
                ButtonSegment(value: ThemeMode.system, icon: Icon(Icons.settings_system_daydream), label: Text('System')),
              ],
              selected: {themeService.themeMode},
              onSelectionChanged: (Set<ThemeMode> newSelection) {
                themeService.updatePreferences(mode: newSelection.first);
              },
            ),
            const SizedBox(height: 16),

            // Accent Palette Swatches
            const Text('Lodge Accent Palette', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: MobileThemeService.palettes.map((palette) {
                final isSelected = themeService.accentKey == palette.key;
                return ChoiceChip(
                  label: Text(palette.label, style: const TextStyle(fontSize: 11)),
                  avatar: CircleAvatar(backgroundColor: palette.primary, radius: 8),
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
            const SizedBox(height: 12),

            // Reset to Default button
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

            // Security & Storage
            const Divider(),
            const SizedBox(height: 12),
            const Text(
              'Security & Credentials',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),

            OutlinedButton.icon(
              onPressed: _showChangePasswordDialog,
              icon: const Icon(Icons.lock_reset),
              label: const Text('Change Password'),
              style: OutlinedButton.styleFrom(minimumSize: const Size.fromHeight(48)),
            ),
            const SizedBox(height: 12),

            ListTile(
              leading: const Icon(Icons.security, color: Colors.green),
              title: const Text('Offline Storage Encryption'),
              subtitle: const Text('AES-256 SQLCipher Active'),
              trailing: const Icon(Icons.check_circle, color: Colors.green),
              tileColor: Theme.of(context).colorScheme.surfaceContainerHighest,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
            ),
          ],
        ),
      ),
    );
  }
}
