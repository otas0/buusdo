# buusdo_companion (Flutter)

Phone + tablet client for companion protocol v1.

## Setup

Use the Flutter SDK at **`~/flutter`** (git clone of the `stable` channel). Put it
on your PATH before any `flutter` command — avoid running several
`flutter --version` processes in parallel while the Dart SDK is still
downloading.

```bash
# SDK (once):
#   git clone --depth 1 -b stable https://github.com/flutter/flutter.git ~/flutter
export PATH="$HOME/flutter/bin:$PATH"

cd mobile/flutter
flutter create --project-name buusdo_companion --org app.buusdo --platforms=android,ios .
flutter pub get
flutter analyze
flutter run   # device or simulator — user-reported gate for 1.1.0
```

## Honesty

- Pair + status + request_scan only.
- No install / inject UI.
- Tablet (≥700dp): status | recent games two-pane layout.
