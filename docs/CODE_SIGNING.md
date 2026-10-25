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

## Notes

- buusdo does not require SIP disable on macOS (C5).
- Never embed private keys in the repo; use CI secrets / local keychain profiles.
