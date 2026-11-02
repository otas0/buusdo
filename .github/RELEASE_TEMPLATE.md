# buusdo $VERSION

GitHub Releases channel. Prefer documenting which asset set this tag ships.

## Preview tags (e.g. v0.1.0) — wheel only

- **No official installer** (`buusdo-setup-*.exe` not attached)
- Assets: `buusdo-$VERSION-py3-none-any.whl`, `SHA256SUMS`, `INSTALL.txt` (optional sdist)
- **Unsigned** by design
- **Windows / Linux / macOS** supported (capabilities differ by OS; macOS config-only). Installer: Windows Inno; others wheel/source
- Kits (**ReShade** / **OptiScaler**) are **self-provided**, not bundled
- **No** DWM HDR injection (Phase 3)
- Feedback: https://github.com/otas0/buusdo/issues

## Future installer tags (e.g. v1.0.0+) — after Windows Inno smoke

- `buusdo-setup-$VERSION.exe` — Inno Setup, **unsigned** (SmartScreen may warn)
- `SHA256SUMS`, `INSTALL.txt`
- Still no Linux/macOS official installers
- Still kits self-provided; still no DWM HDR

> **SmartScreen** (installer builds only): “Windows protected your PC” is expected for unsigned GitHub builds.

## Verify

```bash
shasum -a 256 -c SHA256SUMS
```

## Visual checklist (attach or link)

Frozen screenshots from `scripts/screenshot_release_checklist.py` live under
`docs/fixtures/release_visual_checklist/` (`main_window.png`, `about_dialog.png`,
`tray_icon_sizes.png`). **Re-run before the next tag** if UI chrome changed;
`scripts/check_release_visual_checklist.py` / CI `logo-assets` job enforce presence.

## Not in any current GitHub release

- Authenticode / Microsoft Store (signing deferred until after unsigned Inno smoke)
- Bundled third-party enhancement binaries
- Ray tracing “enabled” claims
- Premature `v1.*` tags (installer smoke must pass first)
