# macOS package track (config-only)

macOS is a **supported** platform with a config-only enhancement path (C5 — no
injection). This note is the Dock/Finder icon checklist for the Mac `.app`
package track (Nuitka / `pyside6-deploy` on Darwin).

## Icon asset

- Source wordmark: `buusdo/assets/logo.png`
- Committed Dock/Finder icon: `buusdo/assets/logo.icns`
- Regenerate on macOS: `python scripts/generate_logo_icns.py` (`sips` + `iconutil`)

`scripts/deploy.sh` prefers `logo.icns` on Darwin when calling `pyside6-deploy`
(`--macos-app-icon`).

## Dock / Finder smoke (manual)

1. Build on a Mac: `uv sync --extra devui && bash scripts/deploy.sh`
2. Locate `dist/*.app` (or the Nuitka app bundle under `dist/`).
3. In Finder, confirm the bundle icon is the **wordmark** (not the default Qt/Python icon).
4. Open the app; confirm Dock tile matches `logo.icns`.
5. Optional: `iconutil -c iconset buusdo/assets/logo.icns -o /tmp/logo.iconset` and spot-check sizes.

## Non-goals (still)

- Not an official macOS installer for preview / `v0.1.x`
- No notarization / Gatekeeper blessing required for this config-only package track
- Do not block Windows Inno / `v1.0.0` on Mac packaging
