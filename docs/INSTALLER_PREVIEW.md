# Installer preview track (unsigned, draft)

**Default branch:** `main`. Phase 3 DWM HDR stays on `phase3/dwm-hdr`.

## Current gates

| Gate | Status rule |
|------|-------------|
| Unsigned Inno CI | `.github/workflows/installer.yml` (`workflow_dispatch`) |
| PE icons | `scripts/verify_pe_icon.py` must see RT_ICON / RT_GROUP_ICON on Setup + `buusdo.exe` |
| Launch smoke | `scripts/smoke_windows_install.ps1` (CI with launch) |
| Explorer wordmark | Optional — prefer user `launch` reports over agent VM/ISO smoke |
| Authenticode | **Off** until Explorer wordmark smoke is OK |
| Draft release | `v0.1.0-installer-preview` stays **`--draft`** (unpublished) |
| `v1.*` | **Forbidden** until STORE_MVP installer smoke + human call |
| `0.1.1` | **Hold** until real `launch` / `scan` Issues are filed and fixed |

### Gate log (agent)

- PE proxy (CI): Setup + `buusdo.exe` have RT_ICON/RT_GROUP_ICON (`types=[3,14]`) on runs `41298050631` / `41298462774`.
- **No real Explorer** from this Mac agent — do **not** `gh release edit --draft=false` yet; do **not** open a `launch` “icon missing” Issue until a Windows Explorer glance fails.
- `attach_draft` defaults to **true** on `installer.yml` (Windows runner uploads; skip laptop artifact pulls).
- PyInstaller dig (`41298050631` miss vs `41298462774` hit): workdir cache **hit** (~41 MB) but Wheel+Inno still ~80 s. Hit log: `Building because …/assets/__init__.py changed` then `…/PySide6/__init__.py changed` — fresh checkout mtimes + new `.venv` invalidate TOCs, so Analysis/PKG/EXE still ~65 s. Fix: cache `dist/payload/buusdo.exe` too and set `BUUSDO_REUSE_CACHED_PAYLOAD=1` to skip rebuild when the exe is restored.
- Actions `logo-assets` on `main`: blocked by **spending limit** — raise at https://github.com/settings/billing/summary then re-run `ci` (agent cannot change billing).
- Phase 3 stays on `phase3/dwm-hdr`. Re-run `uv run python scripts/screenshot_release_checklist.py` before any new tag if UI chrome changes.
- Explorer still **manual**; draft stays unpublished; Authenticode off; no `v1.*` / no `0.1.1` until launch/scan Issues.
- Local UTM **Windows 2** has no guest disk/ISO yet — install a Windows 11 ARM64 ISO before Explorer wordmark smoke (Microsoft software-download).

## Attach artifacts to draft

From a green artifact (or local `dist/`):

```bash
# Download Actions artifact buusdo-windows-installer into dist/
bash scripts/attach_installer_to_draft.sh v0.1.0-installer-preview
```

CI can do the same when `attach_draft=true` on `installer.yml` (default).

## Promote draft → published preview (still not v1)

Only after Explorer wordmark confirmation:

```bash
gh release edit v0.1.0-installer-preview --draft=false
```

Do **not** retag as `v1.*`. Do **not** claim official / Authenticode.

## Icon missing after install

Triage under GitHub label **`launch`** before any feature work — see [FEEDBACK_TRIAGE.md](FEEDBACK_TRIAGE.md).

## Pre-tag chrome

Before any new tag: `python scripts/screenshot_release_checklist.py` if UI chrome changed;
CI `logo-assets` + `check_release_visual_checklist.py` enforce frozen screenshots.
