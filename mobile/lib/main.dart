import 'package:flutter/material.dart';
import 'screens/login_screen.dart';
import 'screens/field_dashboard.dart';
import 'screens/case_list_screen.dart';
import 'screens/note_draft_screen.dart';
import 'screens/profile_screen.dart';

void main() {
  runApp(const CrbclMobileApp());
}

class CrbclMobileApp extends StatelessWidget {
  const CrbclMobileApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'CRBCL Field App',
      theme: ThemeData(
        primarySwatch: Colors.indigo,
        useMaterial3: true,
      ),
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
