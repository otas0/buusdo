# Feedback triage (post v0.1.0 preview)

Channel: [GitHub Issues](https://github.com/otas0/buusdo/issues).  
Labels: `launch`, `scan` (plus defaults).  
Do **not** agent-poll Actions or re-fire `workflow_dispatch` while waiting on feedback.

## 0.1.1 policy

**Fixes only** — no large features. **Do not tag or publish `0.1.1` until** at least one real `launch` / `scan` Issue is filed **and** fixed (or explicitly closed as works-as-designed). Prefer:

1. **`launch`** — cannot start / missing PySide6 / crash on start / **icon missing after install** (Setup / `buusdo.exe` / tray)
2. **`scan`** — Steam library scan hangs, empty, cancel broken  
3. Deploy/uninstall / anti-cheat false positives  
4. Docs / install clarity (kits self-provide)

### Icon missing after install

Triage under **`launch`** (startup/shell presence), not a new feature label:

- Confirm artifact used Setup/`logo.ico` (Explorer shows wordmark on `buusdo-setup-*.exe` and `buusdo.exe`).
- Wheel-only installs use the in-app / tray PNG via `logo_path()` — no PE icon expected.
- macOS Dock mark needs `logo.icns` (Mac package track only).

## Installer track (parallel, not 0.1.1 scope)

Unsigned Inno installer may be built now (Windows / CI `installer` workflow).  
Ship installer on GitHub when smoke passes; tag **`v1.0.0` only then**. Until then keep calling builds **preview**.

Out of band forever for preview:

- Authenticode / SmartScreen reputation  
- Phase 3 DWM HDR (stay isolated on `phase3/dwm-hdr`)  
- Calling the preview an “official release” or tagging `v1.*` early

## Share copy

See [SHARE_BLURB.md](SHARE_BLURB.md) (wordmark `logo.png`, not `brand_mark.png`).
