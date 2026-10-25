# DWM HDR PoC: offline compile + signing draft (phase3 only)

## Scope

- Compile `buusdo/core/dwm_hdr_shaders/sdr_to_hdr_tonemap.hlsl` offline with `fxc` (legacy) or `dxc`.
- **Never** inject into live DWM. Output is a verification artifact under `.buusdo/dwm_hdr_poc/`.
- Branch `phase3/dwm-hdr` only; do not merge until signature + rollback gates exist.

## Compile (Windows SDK)

```bat
:: Prefer dxc when available
dxc -T ps_6_0 -E MainPS -Fo sdr_to_hdr_tonemap.cso sdr_to_hdr_tonemap.hlsl

:: Fallback fxc (older kits)
fxc /T ps_5_0 /E MainPS /Fo sdr_to_hdr_tonemap.cso sdr_to_hdr_tonemap.hlsl
```

Or: `python scripts/compile_dwm_hdr_poc.py --out <game>/.buusdo/dwm_hdr_poc`

## Signing draft (not implemented)

1. Hash `.cso` with SHA-256; record in `manifest.json`.
2. Optional: Authenticode-sign a companion stub DLL **only if** a future loader exists (not in PoC).
3. Verify hash before any future apply step; mismatch → refuse.
4. Rollback: delete PoC dir + restore prior display session (existing `display_session.json` heal path).

## Gates before main merge

- [ ] OS build allow-list
- [ ] User explicit opt-in + C4 copy (no “HDR unlocked” claims)
- [ ] Transactional uninstall tested
- [ ] No DYLD / injection APIs (already C5 on macOS; Windows must stay out of DWM process space)
