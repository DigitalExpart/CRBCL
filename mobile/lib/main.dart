import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'screens/login_screen.dart';
import 'screens/signup_screen.dart';
import 'screens/app_shell.dart';
import 'screens/field_dashboard.dart';
import 'screens/note_draft_screen.dart';
import 'screens/profile_screen.dart';
import 'screens/client_draft_screen.dart';
import 'screens/intake_draft_screen.dart';
import 'screens/visit_draft_screen.dart';
import 'services/theme_service.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(
    ChangeNotifierProvider(
      create: (_) => MobileThemeService(),
      child: const CrbclMobileApp(),
    ),
  );
}

class CrbclMobileApp extends StatelessWidget {
  const CrbclMobileApp({super.key});

  @override
  Widget build(BuildContext context) {
    try {
      final themeService = Provider.of<MobileThemeService>(context);
      return _buildApp(themeService);
    } catch (_) {
      return ChangeNotifierProvider(
        create: (_) => MobileThemeService(),
        child: Builder(
          builder: (ctx) => _buildApp(Provider.of<MobileThemeService>(ctx)),
        ),
      );
    }
  }

  Widget _buildApp(MobileThemeService themeService) {
    return MaterialApp(
      title: 'CRBCL Family Wellness',
      debugShowCheckedModeBanner: false,
      theme: themeService.getLightTheme(),
      darkTheme: themeService.getDarkTheme(),
      themeMode: themeService.themeMode,
      initialRoute: '/login',
      routes: {
        '/login': (context) => const LoginScreen(),
        '/signup': (context) => const SignUpScreen(),
        '/dashboard': (context) => const AppShell(initialTab: 0),
        '/clients': (context) => const AppShell(initialTab: 1),
        '/cases': (context) => const AppShell(initialTab: 2),
        '/offline': (context) => const AppShell(initialTab: 3),
        '/workspace': (context) => const FieldDashboardScreen(),
        '/profile': (context) => const ProfileScreen(),
        '/note-draft': (context) => const NoteDraftScreen(),
        '/client-draft': (context) => const ClientDraftScreen(),
        '/intake-draft': (context) => const IntakeDraftScreen(),
        '/visit-draft': (context) => const VisitDraftScreen(),
      },
    );
  }
}
