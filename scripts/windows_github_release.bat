@echo off
REM One-shot GitHub Windows release build (unsigned). Run on Windows 10/11.
REM Prerequisites: uv or Python 3.11+, Inno Setup 6 (iscc on PATH), Git Bash optional.
setlocal
cd /d "%~dp0\.."

echo === sync ===
where uv >nul 2>&1 && (
  uv sync --extra devui
) || (
  python -m pip install -e ".[devui]"
)

echo === self-test ===
python scripts\mvp_self_test.py || exit /b 1
python scripts\smoke_github_release_gate.py || exit /b 1

echo === package (deploy + Inno; signing skipped) ===
bash scripts/package_windows_inno.sh
if errorlevel 1 exit /b 1

if not exist "dist\buusdo-setup-*.exe" (
  echo FAIL: no dist\buusdo-setup-*.exe — install Inno Setup 6 and ensure pyside6-deploy produced payload.
  exit /b 1
)

for %%F in (dist\buusdo-setup-*.exe) do set SETUP=%%F
echo === smoke %SETUP% ===
powershell -ExecutionPolicy Bypass -File scripts\smoke_windows_install.ps1 -SetupExe "%SETUP%"
if errorlevel 1 exit /b 1

echo.
echo SMOKE OK. Next: tag v1.0.0 and upload dist\ assets to GitHub Release.
echo   git tag v1.0.0
echo   git push origin v1.0.0
echo   gh release create v1.0.0 dist\buusdo-setup-*.exe dist\SHA256SUMS dist\INSTALL.txt -F .github\RELEASE_TEMPLATE.md
endlocal
