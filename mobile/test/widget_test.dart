import 'package:flutter_test/flutter_test.dart';
import 'package:crbcl_mobile/main.dart';

void main() {
  testWidgets('Mobile App renders LoginScreen on launch', (WidgetTester tester) async {
    await tester.pumpWidget(const CrbclMobileApp());
    await tester.pumpAndSettle();

    expect(find.text('CRBCL Field Worker App'), findsOneWidget);
    expect(find.text('Unlock Encrypted Vault'), findsOneWidget);
  });
}
