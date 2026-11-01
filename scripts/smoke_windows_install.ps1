# Post-install smoke for GitHub Windows MVP (unsigned).
# Usage (elevated not required):
#   powershell -ExecutionPolicy Bypass -File scripts/smoke_windows_install.ps1
#   powershell -File scripts/smoke_windows_install.ps1 -SkipLaunch
param(
  [switch]$SkipLaunch,
  [string]$InstallDir = "$env:LOCALAPPDATA\Programs\buusdo",
  [string]$SetupExe = ""
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

function Ok($m) { Write-Host "OK  $m" }
function Fail($m) { Write-Host "FAIL $m" -ForegroundColor Red; exit 1 }

# 1) Packaging inputs exist
$iss = Join-Path $Root "packaging\inno\buusdo.iss"
if (-not (Test-Path $iss)) { Fail "missing $iss" }
Ok "Inno script present"

$logoIco = Join-Path $Root "buusdo\assets\logo.ico"
$logoPng = Join-Path $Root "buusdo\assets\logo.png"
if (-not (Test-Path $logoPng)) { Fail "missing logo.png" }
if (-not (Test-Path $logoIco)) { Fail "missing logo.ico — run scripts/generate_logo_ico.py" }
Ok "logo.png + logo.ico present (check Setup/exe icon in Explorer after install)"

$store = Join-Path $Root "docs\STORE_MVP.md"
if (-not (Test-Path $store)) { Fail "missing STORE_MVP.md" }
Ok "STORE_MVP.md present"

# 2) Version import (dev tree)
$ver = & python -c "from buusdo import __version__; print(__version__)" 2>$null
if (-not $ver) { $ver = "unknown" }
Ok "version=$ver"

# 3) Optional: run setup silently if provided
if ($SetupExe -and (Test-Path $SetupExe)) {
  Ok "running installer $SetupExe"
  Start-Process -FilePath $SetupExe -ArgumentList "/VERYSILENT","/NORESTART","/DIR=`"$InstallDir`"" -Wait
}

$exe = Join-Path $InstallDir "buusdo.exe"
if (Test-Path $exe) {
  Ok "installed exe $exe"
  if (-not $SkipLaunch) {
    $p = Start-Process -FilePath $exe -PassThru
    Start-Sleep -Seconds 3
    if ($p.HasExited -and $p.ExitCode -ne 0) {
      Fail "buusdo exited early code=$($p.ExitCode)"
    }
    if (-not $p.HasExited) {
      Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
    }
    Ok "launch smoke"
  }
} else {
  Write-Host "WARN installed exe not found (build installer on Windows first) — structural checks only"
}

# 4) Uninstall residue check when uninstaller exists
$unins = Get-ChildItem -Path $InstallDir -Filter "unins*.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($unins) {
  Start-Process -FilePath $unins.FullName -ArgumentList "/VERYSILENT","/NORESTART" -Wait
  Start-Sleep -Seconds 2
  if (Test-Path $exe) { Fail "exe still present after uninstall" }
  Ok "uninstall removed exe"
} else {
  Write-Host "WARN no unins*.exe — skip uninstall residue check"
}

Ok "smoke_windows_install finished"
exit 0
