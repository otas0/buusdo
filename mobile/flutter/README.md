# buusdo_companion (Flutter)

Phone + tablet client for companion protocol v1.

## Setup

```bash
# SDK (once): git clone --depth 1 -b stable https://github.com/flutter/flutter.git ~/flutter
# export PATH="$HOME/flutter/bin:$PATH"
cd mobile/flutter
flutter pub get
flutter analyze
flutter run   # device or simulator — user-reported gate for 1.1.0
```

## Honesty

- Pair + status + request_scan only.
- No install / inject UI.
- Tablet (≥700dp): status | recent games two-pane layout.
