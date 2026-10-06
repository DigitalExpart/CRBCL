import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'screens/login_screen.dart';
import 'screens/field_dashboard.dart';
import 'screens/case_list_screen.dart';
import 'screens/note_draft_screen.dart';
import 'screens/profile_screen.dart';
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
    final themeService = Provider.of<MobileThemeService>(context);

    return MaterialApp(
      title: 'CRBCL Field App',
      theme: themeService.getLightTheme(),
      darkTheme: themeService.getDarkTheme(),
      themeMode: themeService.themeMode,
      initialRoute: '/login',
      routes: {
        '/login': (context) => const LoginScreen(),
        '/dashboard': (context) => const FieldDashboardScreen(),
        '/cases': (context) => const CaseListScreen(),
        '/note-draft': (context) => const NoteDraftScreen(),
        '/profile': (context) => const ProfileScreen(),
      },
    );
  }
}
