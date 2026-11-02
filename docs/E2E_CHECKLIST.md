# buusdo developer self-test checklist

Local checks before tagging a preview. No third-party sign-off required —
run what you can on your machine and mark items yourself.

Automated gate: `python scripts/mvp_self_test.py`.

## Common

- [ ] Launch UI (`python -m buusdo`); brand mark + light instrument theme look correct
- [ ] Anti-cheat fixture / real AC game dir → block page, **no** Continue button
- [ ] Config export/import zip round-trips
- [ ] History shows install/uninstall events after a deploy cycle

## Windows (primary MVP)

- [ ] Scan Steam library; Steam user dropdown works with multiple userdata
- [ ] ReShade D3D11: deploy `dxgi.dll`, uninstall restores byte-for-byte
- [ ] ReShade Vulkan: emit `ReShade64.json` + optional bat/registry writeback
- [ ] OptiScaler colliding with deployed ReShade filenames → block
- [ ] Remix enabled → forbid ReShade `d3d9` proxy
- [ ] Display/HDR prefs save to per-game JSON
- [ ] DWM HDR capability shows unavailable (Phase 3 — expected)

## Linux

- [ ] vkBasalt mode writes selected user’s `localconfig.vdf`
- [ ] Goverlay launches when installed; capability unavailable when missing

## Linux Proton

- [ ] Proton games show `[Proton]` badge
- [ ] ReShade writes under `steamapps/common/<game>`, not `pfx/drive_c`
- [ ] Vulkan layer mode writes launch-option hints

## macOS (config-only, C5)

- [ ] Discover GPTK / CrossOver / Bridgeplay config directories
- [ ] MetalFX config writes succeed; copy never claims DLSS trademarks
- [ ] Unconfirmed compat-layer target → default block

## Packaging

- [ ] `bash scripts/package_mvp.sh` writes `dist/*.whl` + `dist/SHA256SUMS` + `dist/INSTALL.txt`
- [ ] Optional: `bash scripts/deploy.sh` when pyside6-deploy/Nuitka is available
