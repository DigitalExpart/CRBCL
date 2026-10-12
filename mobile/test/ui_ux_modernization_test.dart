import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:crbcl_mobile/screens/login_screen.dart';
import 'package:crbcl_mobile/screens/app_shell.dart';
import 'package:crbcl_mobile/screens/home_dashboard_screen.dart';
import 'package:crbcl_mobile/services/theme_service.dart';
import 'package:crbcl_mobile/widgets/status_badge.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    FlutterSecureStorage.setMockInitialValues({});
  });

  group('UI/UX Modernization & Accessibility Widget Tests', () {
    testWidgets('Password visibility toggle toggles between obscure and visible', (WidgetTester tester) async {
      FlutterSecureStorage.setMockInitialValues({});
      await tester.pumpWidget(
        ChangeNotifierProvider(
          create: (_) => MobileThemeService(),
          child: const MaterialApp(home: LoginScreen()),
        ),
      );
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 300));

      // Find password textfield
      final passwordFinder = find.widgetWithText(TextField, 'Password');
      expect(passwordFinder, findsOneWidget);

      final TextField initialTextField = tester.widget<TextField>(passwordFinder);
      expect(initialTextField.obscureText, isTrue, reason: 'Password must be obscured by default');

      final iconFinder = find.byIcon(Icons.visibility_off);
      expect(iconFinder, findsOneWidget);

      await tester.tap(iconFinder);
      await tester.pump();

      // Now password should be visible (Icons.visibility)
      expect(find.byIcon(Icons.visibility), findsOneWidget);
      final TextField toggledTextField = tester.widget<TextField>(passwordFinder);
      expect(toggledTextField.obscureText, isFalse, reason: 'Password should be visible after toggle');
    });

    testWidgets('Offline PIN visibility toggle toggles between obscure and visible', (WidgetTester tester) async {
      FlutterSecureStorage.setMockInitialValues({
        'crbcl_access_token': 'mock_valid_token',
        'crbcl_pin_hash': 'mock_pbkdf2_hash',
      });
      await tester.pumpWidget(
        ChangeNotifierProvider(
          create: (_) => MobileThemeService(),
          child: const MaterialApp(home: LoginScreen()),
        ),
      );
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 300));

      // Find PIN text field
      final pinFinder = find.widgetWithText(TextField, 'Enter 4 or 6-digit PIN');
      expect(pinFinder, findsOneWidget);

      final TextField initialPinField = tester.widget<TextField>(pinFinder);
      expect(initialPinField.obscureText, isTrue, reason: 'PIN must be hidden by default');

      // Tap visibility toggle
      final iconFinder = find.byIcon(Icons.visibility_off);
      expect(iconFinder, findsOneWidget);

      await tester.tap(iconFinder);
      await tester.pump();

      expect(find.byIcon(Icons.visibility), findsOneWidget);
      final TextField toggledPinField = tester.widget<TextField>(pinFinder);
      expect(toggledPinField.obscureText, isFalse, reason: 'PIN must be visible after toggle');
    });

    testWidgets('Login validation shows error banner on empty credentials', (WidgetTester tester) async {
      FlutterSecureStorage.setMockInitialValues({});
      await tester.pumpWidget(
        ChangeNotifierProvider(
          create: (_) => MobileThemeService(),
          child: const MaterialApp(home: LoginScreen()),
        ),
      );
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 300));

      // Tap submit button with empty fields
      final submitFinder = find.text('Authenticate & Register Device');
      expect(submitFinder, findsOneWidget);
      await tester.tap(submitFinder);
      await tester.pump();

      // Should display clear error message
      expect(find.text('Please enter both email and password.'), findsOneWidget);
    });

    testWidgets('Persistent Bottom Navigation renders all 5 tabs and responds to tap', (WidgetTester tester) async {
      FlutterSecureStorage.setMockInitialValues({
        'crbcl_access_token': 'mock_token',
        'crbcl_user_name': 'Jane Caseworker',
      });

      await tester.pumpWidget(
        ChangeNotifierProvider(
          create: (_) => MobileThemeService(),
          child: const MaterialApp(
            home: AppShell(initialTab: 0),
          ),
        ),
      );
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 300));

      // Check all 5 tabs exist
      expect(find.text('Home'), findsOneWidget);
      expect(find.text('Clients'), findsOneWidget);
      expect(find.text('Cases'), findsOneWidget);
      expect(find.text('Offline'), findsOneWidget);
      expect(find.text('More'), findsOneWidget);

      // Tap on Clients tab
      await tester.tap(find.text('Clients'));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 200));

      // Verify Clients screen header rendered
      expect(find.text('Clients • Field Directory'), findsOneWidget);

      // Tap on Offline tab
      await tester.tap(find.text('Offline'));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 200));

      expect(find.textContaining('Offline Workspace'), findsOneWidget);
    });

    testWidgets('Navigation Drawer organizes workflows into MAIN, FIELD OPERATIONS, and ACCOUNT', (WidgetTester tester) async {
      FlutterSecureStorage.setMockInitialValues({
        'crbcl_user_name': 'Sarah Bear',
        'crbcl_user_email': 'sarah.bear@crbcl.org',
        'crbcl_user_roles': '["Caseworker"]',
      });

      await tester.pumpWidget(
        ChangeNotifierProvider(
          create: (_) => MobileThemeService(),
          child: const MaterialApp(
            home: AppShell(initialTab: 0),
          ),
        ),
      );
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 300));

      // Open drawer using hamburger button
      final menuFinder = find.byTooltip('Open navigation menu');
      expect(menuFinder, findsOneWidget);
      await tester.tap(menuFinder);
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 300));

      // Check Drawer contents
      expect(find.text('MAIN'), findsOneWidget);
      expect(find.text('FIELD OPERATIONS'), findsOneWidget);
      expect(find.text('Sarah Bear'), findsOneWidget);
      expect(find.text('Dashboard'), findsOneWidget);
      expect(find.descendant(of: find.byType(Drawer), matching: find.text('Clients')), findsOneWidget);
      expect(find.text('Offline Workspace'), findsOneWidget);
      expect(find.text('New Client Draft'), findsOneWidget);
    });

    testWidgets('Staff Dashboard renders welcome card, quick actions, and sync ledger', (WidgetTester tester) async {
      FlutterSecureStorage.setMockInitialValues({
        'crbcl_user_name': 'Chief Elder Leader',
        'crbcl_user_roles': '["Director"]',
      });

      await tester.pumpWidget(
        ChangeNotifierProvider(
          create: (_) => MobileThemeService(),
          child: MaterialApp(
            home: HomeDashboardScreen(
              onOpenDrawer: () {},
              onNavigateTab: (_) {},
            ),
          ),
        ),
      );
      // Wait for async load to complete
      for (int i = 0; i < 10; i++) {
        await tester.pump(const Duration(milliseconds: 100));
        if (find.byType(CircularProgressIndicator).evaluate().isEmpty) break;
      }

      expect(find.textContaining('Welcome, Chief Elder Leader'), findsOneWidget);
      expect(find.text('Quick Actions'), findsOneWidget);
      expect(find.text('Register Client'), findsOneWidget);
      expect(find.text('New Intake'), findsOneWidget);
      expect(find.text('Case Notes'), findsOneWidget);
      expect(find.text('Home Visits'), findsOneWidget);
      expect(find.text('Synchronization Ledger'), findsOneWidget);
      expect(find.textContaining('Sync Now'), findsOneWidget);
    });

    testWidgets('Responsive Layout renders cleanly at narrow 320px width without overflow', (WidgetTester tester) async {
      tester.view.physicalSize = const Size(320 * 2.0, 640 * 2.0);
      tester.view.devicePixelRatio = 2.0;
      addTearDown(() {
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
      });

      FlutterSecureStorage.setMockInitialValues({});
      await tester.pumpWidget(
        ChangeNotifierProvider(
          create: (_) => MobileThemeService(),
          child: const MaterialApp(home: LoginScreen()),
        ),
      );
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 300));

      expect(find.text('CRBCL Field Operations'), findsOneWidget);
      expect(tester.takeException(), isNull, reason: 'Should have no overflow exceptions at 320px width');
    });

    testWidgets('Dark Mode renders readable text and theme-aware colors', (WidgetTester tester) async {
      final themeService = MobileThemeService();
      await themeService.updatePreferences(mode: ThemeMode.dark);

      await tester.pumpWidget(
        ChangeNotifierProvider.value(
          value: themeService,
          child: MaterialApp(
            theme: themeService.getLightTheme(),
            darkTheme: themeService.getDarkTheme(),
            themeMode: ThemeMode.dark,
            home: const LoginScreen(),
          ),
        ),
      );
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 300));

      final BuildContext context = tester.element(find.byType(LoginScreen));
      final theme = Theme.of(context);

      expect(theme.brightness, equals(Brightness.dark));
      expect(theme.colorScheme.onSurface, equals(CrbclTokens.darkForeground));
      expect(tester.takeException(), isNull);
    });

    testWidgets('StatusBadge handles all 4 states without overflow', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: Column(
              children: [
                StatusBadge(status: 'PENDING'),
                StatusBadge(status: 'SYNCED'),
                StatusBadge(status: 'NEEDS_REVIEW'),
                StatusBadge(status: 'FAILED'),
              ],
            ),
          ),
        ),
      );
      await tester.pump();

      expect(find.text('Pending Sync'), findsOneWidget);
      expect(find.text('Server Verified'), findsOneWidget);
      expect(find.text('Needs Review'), findsOneWidget);
      expect(find.text('Sync Failed'), findsOneWidget);
      expect(tester.takeException(), isNull);
    });
  });
}
