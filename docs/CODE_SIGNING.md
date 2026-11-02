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
