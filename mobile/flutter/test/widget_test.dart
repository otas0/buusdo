import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:buusdo_companion/main.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('companion home loads', (tester) async {
    SharedPreferences.setMockInitialValues({});
    final prefs = await SharedPreferences.getInstance();
    await tester.pumpWidget(BuusdoCompanionApp(prefs: prefs));
    expect(find.textContaining('Pair'), findsOneWidget);
  });
}
