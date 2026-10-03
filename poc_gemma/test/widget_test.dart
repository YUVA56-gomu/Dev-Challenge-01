import 'package:flutter_test/flutter_test.dart';
import 'package:poc_gemma/main.dart';

void main() {
  testWidgets('Gemma POC smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const GemmaPocApp());
    expect(find.text('On-Device Gemma POC'), findsOneWidget);
  });
}
