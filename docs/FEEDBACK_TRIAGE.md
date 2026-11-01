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

Triage under **`launch`** (startup/shell presence) **before** any feature work:

- Confirm artifact used Setup/`logo.ico` (Explorer shows wordmark on `buusdo-setup-*.exe` and `buusdo.exe`).
- PE check: `python scripts/verify_pe_icon.py path\to\buusdo.exe` (expects `RT_GROUP_ICON`).
- Wheel-only installs use the in-app / tray PNG via `logo_path()` — no PE icon expected.
- macOS Dock mark needs `logo.icns` — see [MAC_PACKAGE.md](MAC_PACKAGE.md).

## Installer track (parallel, not 0.1.1 scope)

See [INSTALLER_PREVIEW.md](INSTALLER_PREVIEW.md). Unsigned Inno may be built via `installer.yml`.  
Draft `v0.1.0-installer-preview` stays **unpublished** until Explorer wordmark smoke.  
**Authenticode stays off** until that Explorer check. Tag **`v1.0.0` only** after STORE_MVP smoke.  
Promote draft → published preview (still not v1) is a **human** decision after Explorer OK.

Out of band for preview:

- Authenticode / SmartScreen reputation (until Explorer smoke)  
- Phase 3 DWM HDR (**isolated on `phase3/dwm-hdr`**; default branch is `main`)  
- Calling the preview an “official release” or tagging `v1.*` early  
- Shipping `0.1.1` without real `launch` / `scan` Issues

## Share copy

See [SHARE_BLURB.md](SHARE_BLURB.md) (wordmark `logo.png`, not `brand_mark.png`).
