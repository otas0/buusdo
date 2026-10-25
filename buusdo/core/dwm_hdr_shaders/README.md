# DWM SDR→HDR shader patch PoC (phase3/dwm-hdr only)

This directory holds an **offline** HLSL tone-map stub used by the Phase-3 prototype.

- **Does not** inject into DWM, Desktop Window Manager, or any system process.
- **Does not** ship as a product capability on `main` (`is_available()` stays `False`).
- Materializes a copy under `<game>/.buusdo/dwm_hdr_poc/` only when `BUUSDO_ENABLE_DWM_HDR_PROTOTYPE=1`.

Keep this branch unmerged until the real patch pipeline (signature, rollback, OS gating) exists.
