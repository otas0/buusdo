# Dual-monitor CCD adapterId/targetId recording

Run on a **real dual-monitor Windows** host (this CI/macOS environment cannot capture live CCD IDs).

## Record (on/off) and overwrite fixture

```bat
python scripts/verify_ccd_hdr.py --apply on --record docs/fixtures/ccd_dual_monitor_sample.json --overwrite-fixture --require-multi
python scripts/verify_ccd_hdr.py --apply off --record docs/fixtures/ccd_dual_monitor_sample.json --overwrite-fixture --require-multi
```

After a successful live record, `host_windows` should be `true`, `target_count` ≥ 2, and each `adapter_target_ids[]` entry must include real `adapterLow` / `adapterHigh` / `targetId`. The ILLUSTRATIVE note is replaced by the recorder.

## Validate before commit

```bash
python scripts/validate_ccd_fixture.py docs/fixtures/ccd_dual_monitor_sample.json --require-live
```

`--require-live` fails until `host_windows` is true and the fixture is no longer marked ILLUSTRATIVE.

This macOS/Linux checkout cannot capture live CCD IDs; keep the ILLUSTRATIVE sample until a dual-monitor Windows host overwrites it and the validate gate passes.

Commit checklist after a live record:

```bash
python scripts/validate_ccd_fixture.py docs/fixtures/ccd_dual_monitor_sample.json --require-live
git add docs/fixtures/ccd_dual_monitor_sample.json
git commit -m "Record real dual-monitor CCD adapterId/targetId."
```

Status: still ILLUSTRATIVE on this machine — no dual-monitor Windows host available in CI/dev.
Do not mark `--require-live` green until a real dual-monitor Windows record overwrites adapter/target IDs.
Do not pass `--require-live` until a real dual-monitor overwrite lands.

## Windows host checklist (real dual-monitor)

This macOS/CI agent **cannot** run the live record — copy the block below onto a dual-monitor Windows machine.

1. Attach ≥2 monitors; Windows Settings → System → Display shows both.
2. From a checkout on that host (or double-click `scripts/ccd_record_windows.bat`):

```bat
scripts\ccd_record_windows.bat
REM or manually:
python -m pip install -e ".[dev]"
python scripts/verify_ccd_hdr.py --apply on --record docs/fixtures/ccd_dual_monitor_sample.json --overwrite-fixture --require-multi
python scripts/validate_ccd_fixture.py docs/fixtures/ccd_dual_monitor_sample.json --require-live
```

3. Confirm `host_windows: true`, `target_count` ≥ 2, and real `adapterLow`/`adapterHigh`/`targetId` (not sample placeholders).
4. Commit only the fixture JSON after validate passes.

Preflight on any OS (does **not** overwrite the fixture):

```bash
python scripts/validate_ccd_fixture.py docs/fixtures/ccd_dual_monitor_sample.json
# expect ILLUSTRATIVE / host_windows false until Windows overwrite
```
