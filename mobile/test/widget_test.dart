import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:crbcl_mobile/main.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    FlutterSecureStorage.setMockInitialValues({});
  });

  testWidgets('Mobile App renders LoginScreen on launch', (WidgetTester tester) async {
    FlutterSecureStorage.setMockInitialValues({});
    await tester.pumpWidget(const CrbclMobileApp());
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 200));

    expect(find.text('CRBCL Field Worker App'), findsOneWidget);
    expect(find.text('Unlock Encrypted Vault'), findsOneWidget);
  });
}
