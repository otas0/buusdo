# GitHub release MVP (v1.0.0 gate)

**Channel:** GitHub Releases only (not Microsoft Store, not signed SmartScreen reputation).  
**Primary OS:** Windows. Linux / macOS stay **experimental** source/wheel only — not formal release assets.

## Freeze decisions

| Decision | Choice |
|----------|--------|
| Distribution | GitHub Releases |
| Code signing / Authenticode | **Skipped** (intentionally) |
| SmartScreen / EV-OV / Store | **Out of scope** for this channel |
| Installer | **Inno Setup** (not MSIX) |
| App payload | `pyside6-deploy` / Nuitka → folder or onefile, then Inno wraps it |
| Kits | Still **not** bundled |
| Phase 3 DWM HDR | Still isolated |

## In scope for v1.0.0

1. Windows Inno installer (unsigned) + `SHA256SUMS`
2. In-app **About** (version, license pointer, feedback URL)
3. Post-install smoke: launch, version string, uninstall leaves no app dir
4. Release notes template: support OS, kits self-provide, explicit non-goals
5. Tag `v1.0.0` **only after** installer smoke passes on a Windows machine

## Out of scope

- Authenticode / `signtool` / notarization (hooks may exist but are **not** required)
- Microsoft Store packaging
- Official Linux/macOS installers
- Bundled ReShade / OptiScaler
- Third-party acceptance sign-off

## Build (Windows builder only)

macOS/Linux **cannot** produce `buusdo-setup-*.exe` (needs Inno `iscc` + Windows payload).

```bat
REM one-shot:
scripts\windows_github_release.bat

REM or manual:
uv sync --extra devui
bash scripts/package_windows_inno.sh
powershell -ExecutionPolicy Bypass -File scripts/smoke_windows_install.ps1 -SetupExe dist\buusdo-setup-0.1.0.exe
```

Artifacts under `dist/`: `buusdo-setup-*.exe`, `SHA256SUMS`, `INSTALL.txt`.

**SmartScreen:** unsigned GitHub builds may show “Windows protected your PC”. Expected — document in the Release body; do not block v1.0.0 on reputation.

**Kits:** ReShade / OptiScaler are **not** bundled — users pick kit folders in the UI.  
**DWM HDR:** not in this release (Phase 3 stays isolated).

## After smoke OK → GitHub Release

```bat
git tag v1.0.0
git push origin v1.0.0
gh release create v1.0.0 dist\buusdo-setup-*.exe dist\SHA256SUMS dist\INSTALL.txt -F .github\RELEASE_TEMPLATE.md
```

Do **not** attach Linux/macOS installers. Experimental wheels optional as secondary assets only.

## Preview vs v1.0.0

- **Preview** (`docs/MVP.md`): wheel + self-test is enough.
- **v1.0.0**: this document’s Inno installer smoke must pass on Windows; then tag and attach assets on GitHub.
- **1.0.1**: after first Issues from the GitHub release, not before.
