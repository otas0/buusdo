# buusdo_companion (Flutter)

Phone + tablet client for companion protocol v1.

## Setup

Use the Flutter SDK at **`~/flutter`** (git clone of the `stable` channel). Put it
on your PATH before any `flutter` command — avoid running several
`flutter --version` processes in parallel while the Dart SDK is still
downloading.

```bash
# SDK (once) — prefer brew when the network is healthy; avoid parallel flutter --version.
#   brew install --cask flutter
# Fallback: git clone --depth 1 -b stable … ~/flutter
export PATH="$HOME/flutter/bin:/opt/homebrew/bin:$PATH"

cd mobile/flutter
# android/ios are not committed; generate locally when you need a device build:
flutter create --project-name buusdo_companion --org app.buusdo --platforms=android,ios .
flutter pub get && flutter analyze && flutter run
```

**Speed policy:** do not block product work on local Dart SDK downloads. CI
`flutter-analyze` already checks `lib/`. Pair+status is a human gate
([Issue #13](https://github.com/otas0/buusdo/issues/13)).

## Honesty

- Pair + status + request_scan only.
- No install / inject UI.
- Tablet (≥700dp): status | recent games two-pane layout.
