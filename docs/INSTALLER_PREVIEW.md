# Installer preview track (unsigned, draft)

**Default branch:** `main`. Phase 3 DWM HDR stays on `phase3/dwm-hdr`.

## Current gates

| Gate | Status rule |
|------|-------------|
| Unsigned Inno CI | `.github/workflows/installer.yml` (`workflow_dispatch`) |
| PE icons | `scripts/verify_pe_icon.py` must see RT_ICON / RT_GROUP_ICON on Setup + `buusdo.exe` |
| Launch smoke | `scripts/smoke_windows_install.ps1` (CI with launch) |
| Explorer wordmark | **Manual on Windows** — Setup + `buusdo.exe` show logo, not default Qt |
| Authenticode | **Off** until Explorer wordmark smoke is OK |
| Draft release | `v0.1.0-installer-preview` stays **`--draft`** (unpublished) |
| `v1.*` | **Forbidden** until STORE_MVP installer smoke + human call |
| `0.1.1` | **Hold** until real `launch` / `scan` Issues are filed and fixed |

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
