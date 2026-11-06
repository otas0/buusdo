# MVP freeze (Windows / Linux / macOS)

**Status:** freeze for first public/dev preview. Scope below is intentional.

For the **GitHub v1.0.0 installer** gate (Inno, unsigned), see [STORE_MVP.md](STORE_MVP.md).

## In scope

- **Windows:** Steam library scan → ReShade deploy / uninstall with **transactional** restore
- **Linux:** vkBasalt / Goverlay scheduling; Proton prefix ReShade deploy where applicable
- **macOS:** MetalFX compatibility-layer config only (C5 — no injection)
- Anti-cheat hard block (C1) — no continue-anyway
- Honest copy (C4) — no “ray tracing enabled”, no DLSS claims on macOS
- Hardware honesty rows ([HARDWARE_NOTES.md](HARDWARE_NOTES.md)) — not product boosts
- Mobile companion foundation ([MOBILE.md](MOBILE.md)) — status/scan request only; ships toward [RELEASE_1.1.0.md](RELEASE_1.1.0.md)
- Developer self-test (local), not third-party acceptance sign-off
- Distributable **wheel / sdist** under `dist/` with `SHA256SUMS` + three-step install notes
- Optional host binary via `scripts/deploy.sh` (pyside6-deploy) when the toolchain is present

## Out of scope (do not block ship)

- Phase 3 DWM HDR live injection (`phase3/dwm-hdr` stays isolated)
- Dual-monitor CCD live fixture overwrite (ILLUSTRATIVE until a Windows host records)
- Feature **parity** across OS (capabilities differ by platform — that is intentional)
- Codesign / notarization / SmartScreen reputation (document UNSIGNED; **cancelled** — see [CODE_SIGNING.md](CODE_SIGNING.md) / [PROJECT_COMPLETE.md](PROJECT_COMPLETE.md))
- Agent polling of GitHub Actions; after Billing fix → **one** `workflow_dispatch` only

## Kits

ReShade / OptiScaler binaries are **not** bundled. Users point the UI (or config) at their own kit folders.

## Self-test

```bash
uv sync --extra devui
python scripts/mvp_self_test.py
# optional package:
bash scripts/package_mvp.sh
```

## Platforms

| Platform | MVP label |
|----------|-----------|
| Windows  | **supported** (fullest surface: ReShade / OptiScaler / display) |
| Linux    | **supported** (vkBasalt / Goverlay / Proton path) |
| macOS    | **supported** (config-only MetalFX compat; C5) |
