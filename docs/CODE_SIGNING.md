# Code signing

**Status (2026-11):** prep track **started**. Unsigned Inno draft remains the default
ship path. Do **not** attach signed Setup/`buusdo.exe` to the draft release until
Explorer wordmark smoke on Setup + `buusdo.exe` is confirmed.

Checklist before first signed artifact:

1. [ ] Code-signing cert available (EV preferred for SmartScreen)
2. [ ] `scripts/codesign.env` present locally (gitignored) — see `codesign.env.example` if present
3. [ ] Unsigned draft Setup from `installer.yml` still attaches as `--draft`
4. [x] Explorer wordmark OK on Setup + `buusdo.exe` (human, 2026-11-02)
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

## macOS (Developer ID + Notarization + Staple)

**Blocker (2026-11-02):** this builder has **0** codesigning identities
(`security find-identity -v -p codesigning`). Signing cannot run until a
**Developer ID Application** certificate is installed from an Apple Developer
Program account, plus a `notarytool` keychain profile.

### One-shot (preferred)

```bash
cp scripts/codesign.env.example scripts/codesign.env
# Edit CODESIGN_IDENTITY + NOTARY_PROFILE to real values (gitignored)

# Store notary credentials once (app-specific password or API key):
xcrun notarytool store-credentials "buusdo-notary" \
  --apple-id "you@example.com" --team-id "TEAMID" --password "app-specific-password"

chmod +x scripts/sign_and_notarize_macos.sh
bash scripts/sign_and_notarize_macos.sh
# → dist/buusdo-macos-$VERSION.zip (signed, notarized, stapled)
```

### Manual steps

1. Sign the `.app` with Developer ID Application (hardened runtime + timestamp):

```bash
codesign --deep --force --options runtime --timestamp \
  --sign "Developer ID Application: <Name> (TEAMID)" \
  dist/macos/Buusdo.app
```

2. Notarize + staple:

```bash
ditto -c -k --keepParent dist/macos/Buusdo.app dist/buusdo-notarize.zip
xcrun notarytool submit dist/buusdo-notarize.zip --keychain-profile "buusdo-notary" --wait
xcrun stapler staple dist/macos/Buusdo.app
spctl --assess --type execute dist/macos/Buusdo.app
```

3. Replace the GitHub Release macOS zip + refresh `SHA256SUMS` (release stays published).

## Local hook (Windows / thin macOS)

```bash
cp scripts/codesign.env.example scripts/codesign.env
chmod +x scripts/codesign_hooks.sh
./scripts/codesign_hooks.sh dist/macos/Buusdo.app   # or .exe on Windows
```

Prefer `scripts/sign_and_notarize_macos.sh` for the full Apple Gatekeeper path.
CI never receives private keys from the repo.

## CI gate (Authenticode)

`installer.yml` stays **unsigned by default**. Optional `workflow_dispatch` inputs:

| Input | Default | Role |
|-------|---------|------|
| `attach_draft` | `true` | Attach Setup + SHA256SUMS to draft preview (unpublished) |
| `explorer_wordmark_ok` | `false` | Human confirmed Explorer wordmark on Setup + `buusdo.exe` |
| `sign_authenticode` | `false` | Request Authenticode path (fail-closed) |

When `sign_authenticode=true`, the job **exits 1** unless both:

1. `explorer_wordmark_ok=true`, and
2. repo secrets `WINDOWS_CERT_PFX` + `WINDOWS_CERT_PASSWORD` are set.

Do **not** replace draft assets with signed binaries until that gate passes and a human reviews the throwaway dry-run. Keep the draft unpublished.

Local dry-run (no draft replace):

```bash
cp scripts/codesign.env.example scripts/codesign.env   # fill real values; gitignored
# On Windows signing host, copy Setup/exe aside then:
./scripts/codesign_hooks.sh /path/to/throwaway/buusdo.exe
```

Without `scripts/codesign.env` / cert, the hook must fail closed — that is expected.

After every successful `attach_draft`, `installer.yml` downloads the attached draft Setup and
re-runs `scripts/verify_pe_icon.py` (PE resource presence only — **not** Explorer wordmark).

## Notes

- buusdo does not require SIP disable on macOS (C5).
- Never embed private keys in the repo; use CI secrets / local keychain profiles.
- `scripts/codesign.env`, `*.p12`, and `*.pfx` are gitignored.
