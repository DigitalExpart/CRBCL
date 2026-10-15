import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:crbcl_mobile/screens/login_screen.dart';
import 'package:crbcl_mobile/screens/signup_screen.dart';
import 'package:crbcl_mobile/screens/app_shell.dart';
import 'package:crbcl_mobile/screens/home_dashboard_screen.dart';
import 'package:crbcl_mobile/services/theme_service.dart';
import 'package:crbcl_mobile/screens/admin_login_screen.dart';
import 'package:crbcl_mobile/screens/admin_dashboard_screen.dart';
import 'package:crbcl_mobile/screens/forgot_password_screen.dart';
import 'package:crbcl_mobile/services/auth_service.dart';
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
      final pinFinder = find.widgetWithText(TextField, 'Enter 6-digit PIN');
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

    testWidgets('Login screen displays Sign Up link and removes Server Connection Settings', (WidgetTester tester) async {
      FlutterSecureStorage.setMockInitialValues({});
      await tester.pumpWidget(
        ChangeNotifierProvider(
          create: (_) => MobileThemeService(),
          child: const MaterialApp(home: LoginScreen()),
        ),
      );
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 300));

      // Sign Up link must be present
      expect(find.text('Sign Up'), findsOneWidget);
      // Server Connection Settings must be removed
      expect(find.text('Server Connection Settings'), findsNothing);
      expect(find.text('Backend URL'), findsNothing);
    });

    testWidgets('SignUpScreen renders all required registration inputs matching web version', (WidgetTester tester) async {
      await tester.pumpWidget(
        ChangeNotifierProvider(
          create: (_) => MobileThemeService(),
          child: const MaterialApp(home: SignUpScreen()),
        ),
      );
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 300));

      expect(find.text('Create your account'), findsOneWidget);
      expect(find.text('Sign up to get started'), findsOneWidget);
      expect(find.text('Continue with Google'), findsOneWidget);
      // Labels appear as full labelText strings
      expect(find.textContaining('First Name'), findsWidgets);
      expect(find.textContaining('Last Name'), findsWidgets);
      expect(find.textContaining('Department / Work Unit'), findsOneWidget);
      expect(find.textContaining('Requested Staff Role / Position'), findsOneWidget);
      expect(find.textContaining('Work Email'), findsOneWidget);
      expect(find.text('Create account'), findsOneWidget);
      expect(find.text('Log in'), findsOneWidget);
    });

    testWidgets('AdminLoginScreen renders IT Admin portal and security controls', (WidgetTester tester) async {
      await tester.pumpWidget(
        ChangeNotifierProvider(
          create: (_) => MobileThemeService(),
          child: const MaterialApp(home: AdminLoginScreen()),
        ),
      );
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 300));

      expect(find.text('IT Admin Portal'), findsOneWidget);
      expect(find.textContaining('Restricted sign-in'), findsOneWidget);
      expect(find.text('Forgot password?'), findsOneWidget);
      expect(find.text('Go to Standard Portal'), findsOneWidget);
    });

    testWidgets('ForgotPasswordScreen renders password reset interface matching web version', (WidgetTester tester) async {
      await tester.pumpWidget(
        ChangeNotifierProvider(
          create: (_) => MobileThemeService(),
          child: const MaterialApp(home: ForgotPasswordScreen()),
        ),
      );
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 300));

      expect(find.text('Reset password'), findsOneWidget);
      expect(find.text('Send Reset Link'), findsOneWidget);
      expect(find.textContaining('Back to'), findsWidgets);
    });

    testWidgets('PIN security isolates PIN hashes between different user accounts', (WidgetTester tester) async {
      final auth = MobileAuthService();
      
      // Store PIN for caseworker account
      await auth.setPin('112233', email: 'caseworker@crbcl.org');
      
      // Verify caseworker PIN verifies successfully for caseworker
      final cwResult = await auth.unlockWithPin('112233', email: 'caseworker@crbcl.org');
      expect(cwResult.success, isTrue, reason: 'Caseworker PIN must verify for caseworker account');
      
      // Verify that caseworker PIN does NOT unlock admin account
      final adminResult = await auth.unlockWithPin('112233', email: 'admin@crbcl.org');
      expect(adminResult.success, isFalse, reason: 'Caseworker PIN must NOT unlock admin account');
      
      // Verify admin account has no PIN set initially
      final adminHasPin = await auth.hasUserPin('admin@crbcl.org');
      expect(adminHasPin, isFalse, reason: 'Admin account must not inherit caseworker PIN');
      
      final cwHasPin = await auth.hasUserPin('caseworker@crbcl.org');
      expect(cwHasPin, isTrue, reason: 'Caseworker must retain their own PIN');
    });

    testWidgets('Admin user can authenticate and dashboard reflects Administrator role', (WidgetTester tester) async {
      FlutterSecureStorage.setMockInitialValues({
        'crbcl_user_name': 'Chief IT Admin',
        'crbcl_user_roles': '["admin"]',
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
      for (int i = 0; i < 10; i++) {
        await tester.pump(const Duration(milliseconds: 100));
        if (find.byType(CircularProgressIndicator).evaluate().isEmpty) break;
      }

      expect(find.textContaining('Welcome, Chief IT Admin'), findsOneWidget);
      expect(find.text('admin'), findsOneWidget);
    });

    testWidgets('AdminDashboardScreen allows tapping Invite Staff and opening Create Active Staff Account dialog', (WidgetTester tester) async {
      FlutterSecureStorage.setMockInitialValues({
        'crbcl_user_name': 'System Administrator',
        'crbcl_user_email': 'admin@crbcl.ca',
        'crbcl_user_roles': '["admin"]',
      });

      await tester.pumpWidget(
        ChangeNotifierProvider(
          create: (_) => MobileThemeService(),
          child: const MaterialApp(
            home: AdminDashboardScreen(),
          ),
        ),
      );
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 300));

      // Switch to Staff Access tab
      await tester.tap(find.text('Staff Access'));
      await tester.pumpAndSettle();

      // Find and tap Invite Staff button
      expect(find.text('Invite Staff'), findsOneWidget);
      await tester.tap(find.text('Invite Staff'), warnIfMissed: false);
      await tester.pumpAndSettle();

      // Verify full modal rendered with no dropdown assertion errors
      expect(find.text('Create Active Staff Account'), findsOneWidget);
      expect(find.text('Staff Full Name'), findsOneWidget);
      expect(find.text('Work Email Address'), findsOneWidget);
      expect(find.text('Generate Strong Password'), findsOneWidget);
      expect(tester.takeException(), isNull);
    });

    testWidgets('AdminDashboardScreen allows tapping Team Access and picking from available 24 teams', (WidgetTester tester) async {
      FlutterSecureStorage.setMockInitialValues({
        'crbcl_user_name': 'System Administrator',
        'crbcl_user_email': 'admin@crbcl.ca',
        'crbcl_user_roles': '["admin"]',
      });

      await tester.pumpWidget(
        ChangeNotifierProvider(
          create: (_) => MobileThemeService(),
          child: const MaterialApp(
            home: AdminDashboardScreen(),
          ),
        ),
      );
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 300));

      // Switch to Staff Access tab and open Invite Staff
      await tester.tap(find.text('Staff Access'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Invite Staff'), warnIfMissed: false);
      await tester.pumpAndSettle();

      // Verify Team Access field is present
      await tester.ensureVisible(find.text('Choose'));
      await tester.pumpAndSettle();
      expect(find.text('Team Access & Workspace Permissions'), findsOneWidget);
      expect(find.text('Choose'), findsOneWidget);

      // Tap on Team Access to open the Team Workspace Access selection sheet
      await tester.tap(find.text('Choose'));
      await tester.pumpAndSettle();

      // Verify modal opened with 24 teams list
      expect(find.text('Team Workspace Access'), findsOneWidget);
      expect(find.text('All Teams (Full Workspace Access)'), findsOneWidget);
      expect(find.text('Executive Leadership'), findsOneWidget);
      expect(find.text('Child & Family Services'), findsOneWidget);

      // Search for a specific team
      final searchFinder = find.byType(TextField).last;
      await tester.enterText(searchFinder, 'Sacred');
      await tester.pumpAndSettle();
      expect(find.text('Sacred Wolf Lodge'), findsOneWidget);

      // Apply selection
      await tester.ensureVisible(find.textContaining('Apply'));
      await tester.pumpAndSettle();
      await tester.tap(find.textContaining('Apply'));
      await tester.pumpAndSettle();

      // Verify back in Create Active Staff Account dialog without error
      expect(find.text('Create Active Staff Account'), findsOneWidget);
      expect(tester.takeException(), isNull);
    });
  });
}
