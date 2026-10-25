# buusdo end-to-end manual checklist

## Common
- [ ] Launch UI; logo and dark theme look correct
- [ ] Anti-cheat game directory → block page appears, no Continue button
- [ ] Config export/import zip round-trips successfully
- [ ] History shows install/uninstall events

## Windows
- [ ] Scan Steam library; Steam user dropdown works with multiple userdata
- [ ] ReShade D3D11: deploy `dxgi.dll`, uninstall restores byte-for-byte
- [ ] ReShade Vulkan: emit `ReShade64.json` + bat/registry writeback (optional)
- [ ] OptiScaler colliding with deployed ReShade filenames → block
- [ ] Remix enabled → forbid ReShade `d3d9` proxy
- [ ] Display/HDR prefs save to per-game JSON
- [ ] DWM HDR capability shows unavailable (Phase 3)

## Linux (native)
- [ ] vkBasalt mode writes selected user’s `localconfig.vdf`
- [ ] Goverlay launches when installed; capability unavailable when missing

## Linux (Proton)
- [ ] Proton games show `[Proton]` badge
- [ ] ReShade writes under `steamapps/common/<game>`, not `pfx/drive_c`
- [ ] Vulkan layer mode writes launch-option hints

## macOS
- [ ] Discover GPTK / CrossOver config directories
- [ ] MetalFX config writes succeed; copy never claims DLSS trademarks
- [ ] Unconfirmed compat-layer target → default block
