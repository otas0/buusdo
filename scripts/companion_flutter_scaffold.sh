#!/usr/bin/env bash
# Generate android/ios under mobile/flutter and enable cleartext LAN HTTP (honesty).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP="$ROOT/mobile/flutter"
cd "$APP"

flutter create --project-name buusdo_companion --org app.buusdo --platforms=android,ios .

python3 <<'PY'
from pathlib import Path

app = Path(".").resolve()

# Android cleartext for companion LAN HTTP.
nsc = app / "android/app/src/main/res/xml/network_security_config.xml"
nsc.parent.mkdir(parents=True, exist_ok=True)
nsc.write_text(
    """<?xml version="1.0" encoding="utf-8"?>
<!-- Companion v1 uses cleartext LAN HTTP; see docs/MOBILE.md. -->
<network-security-config>
    <base-config cleartextTrafficPermitted="true" />
</network-security-config>
""",
    encoding="utf-8",
)

manifest = app / "android/app/src/main/AndroidManifest.xml"
text = manifest.read_text(encoding="utf-8")
if "android:usesCleartextTraffic" not in text:
    text = text.replace(
        "<application",
        '<application\n        android:usesCleartextTraffic="true"\n'
        '        android:networkSecurityConfig="@xml/network_security_config"',
        1,
    )
    manifest.write_text(text, encoding="utf-8")

# iOS ATS: allow cleartext LAN (no store TLS claim).
plist = app / "ios/Runner/Info.plist"
pt = plist.read_text(encoding="utf-8")
if "NSAllowsArbitraryLoads" not in pt:
    insert = """\t<key>NSAppTransportSecurity</key>
\t<dict>
\t\t<key>NSAllowsArbitraryLoads</key>
\t\t<true/>
\t</dict>
"""
    pt = pt.replace("</dict>\n</plist>", insert + "</dict>\n</plist>", 1)
    plist.write_text(pt, encoding="utf-8")

# flutter create drops a stock widget_test that references MyApp — replace it.
test = app / "test/widget_test.dart"
test.parent.mkdir(parents=True, exist_ok=True)
test.write_text(
    """import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:buusdo_companion/main.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('companion home loads', (tester) async {
    SharedPreferences.setMockInitialValues({});
    final prefs = await SharedPreferences.getInstance();
    await tester.pumpWidget(BuusdoCompanionApp(prefs: prefs));
    expect(find.textContaining('buusdo'), findsWidgets);
  });
}
""",
    encoding="utf-8",
)

print("OK scaffold + cleartext LAN HTTP")
PY
