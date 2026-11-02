# buusdo

<p align="center">
  <img src="buusdo/assets/logo.png" alt="buusdo wordmark" width="280" />
</p>

Cross-platform graphics enhancement **scheduler + config coordinator** (Windows / Linux / macOS).

It reuses each platform’s existing enhancement stack. It does not implement rendering beyond the injection host, does not implement ray tracing, and is not a game-mod authoring tool.

**MVP preview:** Windows, Linux, and macOS are supported targets (capabilities differ by OS; macOS is config-only).
Latest preview release: [v0.1.0](https://github.com/otas0/buusdo/releases/tag/v0.1.0) (wheel only; no official installer — **not** v1 / not an official release).
Scope freeze: [docs/MVP.md](docs/MVP.md). GitHub v1 installer (Inno, **unsigned**): [docs/STORE_MVP.md](docs/STORE_MVP.md).
Mac Dock icon track: [docs/MAC_PACKAGE.md](docs/MAC_PACKAGE.md).
Installer preview draft (unsigned): [docs/INSTALLER_PREVIEW.md](docs/INSTALLER_PREVIEW.md).
Full constraints: [docs/PROJECT.md](docs/PROJECT.md).

**Share blurb** (also [docs/SHARE_BLURB.md](docs/SHARE_BLURB.md); wordmark above, not the old pixel mark):
buusdo preview — BYO ReShade/OptiScaler kits · Windows / Linux / macOS · https://github.com/otas0/buusdo/releases/tag/v0.1.0

**0.1.1:** ship **only after** `launch` / `scan` Issues are filed and fixed (fixes-only). Installer track is separate → future `v1.0.0` after unsigned Inno smoke. Authenticode deferred; do not tag `v1.*` early.

## End-user install (three steps)

1. Install Python 3.11+ and get a wheel from a release/`dist/` build (`buusdo-*.whl`).
2. Install and launch:

```bash
python -m pip install ./buusdo-*.whl
python -m pip install "PySide6-Essentials==6.12.0"   # UI
python -m buusdo
```

3. In the UI, choose your **ReShade / OptiScaler kit** folders (third-party binaries are not bundled).

Verify: `shasum -a 256 -c dist/SHA256SUMS` (or `sha256sum -c`).

Developer self-test (no third-party acceptance): `python scripts/mvp_self_test.py`  
Wheel package: `bash scripts/package_mvp.sh`  
Windows Inno installer (**Windows builder only**, unsigned; SmartScreen may warn):
`scripts\windows_github_release.bat` or `bash scripts/package_windows_inno.sh`  
Kits are self-provided; DWM HDR is not in the GitHub v1 release ([docs/STORE_MVP.md](docs/STORE_MVP.md)).

## Development

```bash
# Prefer uv (Homebrew Python on this machine may have a broken platform.mac_ver)
uv venv --python 3.12 .venv
source .venv/bin/activate
# Canonical once lock consumers standardize:
uv sync --extra devui
# Equivalent editable path:
#   uv pip install -e ".[devui]"
pytest
python scripts/mvp_self_test.py
python -m buusdo
```

## Architecture

- `core/` — platform detection, Steam discovery, ReShade deploy, anti-cheat gate, transactional writes
- `backends/` — platform-specific implementations (the only places allowed to branch on platform, plus `platform_detect`)
- `ui/` — PySide6; depends only on `EnhancementBackend`; anti-cheat blocks are non-bypassable

## ReShade / OptiScaler kits

Third-party binaries are not bundled. Pick kit folders in the UI, or:

```python
from buusdo.core.config_store import set_reshade_kit_path, set_optiscaler_kit_path
set_reshade_kit_path("/path/to/reshade_kit")
set_optiscaler_kit_path("/path/to/optiscaler_kit")
```

- D3D/OpenGL: proxy DLL; Vulkan: explicit-layer JSON + launch-option hints
- Linux Proton: deploy under `steamapps/common/<game>`; vkBasalt can write back `localconfig.vdf`
- macOS: MetalFX compatibility-layer config only (GPTK / CrossOver / Bridgeplay)

```bash
python scripts/check_no_platform_branch.py   # C3 lint
./scripts/deploy.sh                          # pyside6-deploy packaging skeleton
```

## Steam URI probe (UI)

After **Clear cache now**, use **Try open first**; if that candidate fails, **Try next (N left)**
(or **Ctrl+N** while that button is enabled) walks the remaining deep-link schemes for the
selected game without clearing the list. The button tooltip previews the next URI candidate.

## CI, artifacts, and billing failures

GitHub Actions artifacts (`dwm-hdr-poc`, Qt diag tarballs) and common failure modes
(artifact quota, 0-step jobs from Actions spending limits, Bearer token prune) are
documented in [docs/CI_ARTIFACTS.md](docs/CI_ARTIFACTS.md).

After fixing Billing, **one** `workflow_dispatch` is enough — do not poll Actions from agents.
Billing awareness for local machines: **LaunchAgent only** (`install_watch_ci_billing_launchd.sh`); do not agent-poll Actions.

Quick local checks:

```bash
python scripts/watch_ci_billing.py --notify --once   # exit 1 if newest run looks billing-blocked
bash scripts/install_watch_ci_billing_launchd.sh     # hourly macOS LaunchAgent (appending logs)
bash scripts/assert_watch_ci_billing_log_append.sh    # kickstart + exit-after-timestamp assert
python scripts/verify_dwm_hdr_poc_local.py            # offline zip + hlsl_sha256 (no network)
python scripts/verify_dwm_hdr_poc_local.py --json     # machine-readable summary
bash scripts/push_when_online.sh                     # finite-retry git push (flaky HTTPS)
```

Optional weekly Monday assert (LaunchAgent — still no Actions poll):

```bash
bash scripts/install_assert_watch_ci_billing_weekly.sh
# or crontab: 0 9 * * 1 cd /path/to/buusdo && bash scripts/assert_watch_ci_billing_log_append.sh >>~/Library/Logs/buusdo/assert-cron.log 2>&1
```
