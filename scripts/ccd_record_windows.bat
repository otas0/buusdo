@echo off
REM Live dual-monitor CCD record — run on a real Windows host with >=2 displays.
REM See docs/fixtures/CCD_RECORD.md
setlocal
cd /d "%~dp0\.."
python -m pip install -e ".[dev]"
python scripts/verify_ccd_hdr.py --apply on --record docs/fixtures/ccd_dual_monitor_sample.json --overwrite-fixture --require-multi
if errorlevel 1 exit /b 1
python scripts/validate_ccd_fixture.py docs/fixtures/ccd_dual_monitor_sample.json --require-live
if errorlevel 1 exit /b 1
echo Fixture ready. Commit docs/fixtures/ccd_dual_monitor_sample.json after review.
endlocal
