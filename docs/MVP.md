# MVP freeze (Windows-first)

**Status:** freeze for first public/dev preview. Scope below is intentional.

For the **GitHub v1.0.0 installer** gate (Inno, unsigned), see [STORE_MVP.md](STORE_MVP.md).

## In scope

- Windows: Steam library scan → ReShade deploy / uninstall with **transactional** restore
- Anti-cheat hard block (C1) — no continue-anyway
- Honest copy (C4) — no “ray tracing enabled”, no DLSS claims on macOS
- Developer self-test (local), not third-party acceptance sign-off
- Distributable **wheel / sdist** under `dist/` with `SHA256SUMS` + three-step install notes
- Optional host binary via `scripts/deploy.sh` (pyside6-deploy) when the toolchain is present

## Out of scope (do not block ship)

- Phase 3 DWM HDR live injection (`phase3/dwm-hdr` stays isolated)
- Dual-monitor CCD live fixture overwrite (ILLUSTRATIVE until a Windows host records)
- Feature parity Linux / macOS (ship as **experimental**)
- Codesign / notarization / SmartScreen reputation (document UNSIGNED; sign later)
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
| Windows  | **supported** (primary) |
| Linux    | experimental |
| macOS    | experimental (config-only, C5) |
