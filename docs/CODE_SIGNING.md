# Code signing

## Windows (Authenticode)

1. Obtain a code-signing certificate (EV recommended for SmartScreen).
2. Build with `scripts/deploy.sh` / `pyside6-deploy` → `.exe`.
3. Sign:

```bat
signtool sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 /a dist\buusdo.exe
signtool verify /pa dist\buusdo.exe
```

4. Publish `SHA256SUMS` alongside the binary (CI release workflow already generates checksums for `dist/`).

## macOS (Hardened Runtime + Notarization)

1. Sign the `.app` with Developer ID Application:

```bash
codesign --deep --force --options runtime \
  --sign "Developer ID Application: <Team>" \
  dist/buusdo.app
```

2. Staple after notarization:

```bash
xcrun notarytool submit dist/buusdo.zip --keychain-profile "AC_PROFILE" --wait
xcrun stapler staple dist/buusdo.app
spctl --assess --type execute dist/buusdo.app
```

## Local hook (preferred)

```bash
# Create gitignored scripts/codesign.env with CODESIGN_IDENTITY / NOTARY_PROFILE / SIGNTOOL
cp scripts/codesign.env.example scripts/codesign.env   # if present
chmod +x scripts/codesign_hooks.sh
./scripts/codesign_hooks.sh dist/buusdo.app   # or .exe on Windows
```

Release packaging may call the same hook after `scripts/deploy.sh` when local secrets exist. CI never receives private keys from the repo.

## Notes

- buusdo does not require SIP disable on macOS (C5).
- Never embed private keys in the repo; use CI secrets / local keychain profiles.
- `scripts/codesign.env`, `*.p12`, and `*.pfx` are gitignored.
