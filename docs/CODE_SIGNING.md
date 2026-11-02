# Code signing

**Status (2026-11):** prep track **started**. Unsigned Inno draft remains the default
ship path. Do **not** attach signed Setup/`buusdo.exe` to the draft release until
Explorer wordmark smoke on Setup + `buusdo.exe` is confirmed.

Checklist before first signed artifact:

1. [ ] Code-signing cert available (EV preferred for SmartScreen)
2. [ ] `scripts/codesign.env` present locally (gitignored) — see `codesign.env.example` if present
3. [ ] Unsigned draft Setup from `installer.yml` still attaches as `--draft`
4. [ ] Explorer wordmark OK on Setup + `buusdo.exe`
5. [ ] `signtool` / `codesign_hooks.sh` dry-run on a throwaway copy
6. [ ] Only then replace draft assets with signed ones (still unpublished until human promote)

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
