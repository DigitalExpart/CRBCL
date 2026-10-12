import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:crbcl_mobile/main.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    FlutterSecureStorage.setMockInitialValues({});
  });

  testWidgets('Mobile App renders LoginScreen on launch in online sign-in mode when no saved credentials', (WidgetTester tester) async {
    FlutterSecureStorage.setMockInitialValues({});
    await tester.pumpWidget(const CrbclMobileApp());
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 300));

    expect(find.text('CRBCL Field Operations'), findsOneWidget);
    expect(find.text('CRBCL Staff Sign In'), findsOneWidget);
    expect(find.text('Authenticate & Register Device'), findsOneWidget);
  });

  testWidgets('Mobile App renders Quick PIN Access when credentials and PIN exist', (WidgetTester tester) async {
    FlutterSecureStorage.setMockInitialValues({
      'crbcl_access_token': 'mock_token_xyz',
      'crbcl_pin_hash': 'mock_hash_123',
    });
    await tester.pumpWidget(const CrbclMobileApp());
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 300));

    expect(find.text('CRBCL Field Operations'), findsOneWidget);
    expect(find.text('Quick Offline Access'), findsOneWidget);
    expect(find.text('Unlock Vault'), findsOneWidget);
  });
}
