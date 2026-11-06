# buusdo_companion (Flutter)

Phone + tablet client for companion protocol v1.

## GitHub packages

- **Source** (with `android/` + `ios/`): this tree.
- **Android APK** (unsigned): GitHub Actions workflow `companion-apk` → artifact
  `buusdo-companion.apk`, also attachable to Releases. Not a Play Store build.
- **iOS**: platform sources only on GitHub. An installable IPA needs an Apple
  signing identity (not shipped unsigned like the desktop macOS zip).

## Setup

```bash
export PATH="$HOME/flutter/bin:/opt/homebrew/bin:$PATH"
cd mobile/flutter
# If android/ios are missing locally:
bash ../../scripts/companion_flutter_scaffold.sh
flutter pub get && flutter analyze
flutter run                 # device / emulator
flutter build apk --release # → build/app/outputs/flutter-apk/app-release.apk
```

**Cleartext LAN HTTP** is enabled on Android/iOS for companion v1 (see
`docs/MOBILE.md`). Do not treat this as production TLS.

## Honesty

- Pair + status + request_scan only.
- No install / inject UI.
- Tablet (≥700dp): status | recent games two-pane layout.
- No App Store / Play Store listing in 1.1.x.
