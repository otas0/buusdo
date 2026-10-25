# buusdo

Cross-platform graphics enhancement **scheduler + config coordinator** (Windows / Linux / macOS).

It reuses each platform’s existing enhancement stack. It does not implement rendering beyond the injection host, does not implement ray tracing, and is not a game-mod authoring tool.

Full product semantics and hard constraints: [docs/PROJECT.md](docs/PROJECT.md).

## Development

```bash
# Prefer uv (Homebrew Python on this machine may have a broken platform.mac_ver)
uv venv --python 3.12 .venv
source .venv/bin/activate
uv pip install -e ".[dev,ui]"
pytest
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
walks the remaining deep-link schemes for the selected game without clearing the list.

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
python scripts/verify_dwm_hdr_poc_local.py            # offline zip + hlsl_sha256 (no network)
python scripts/verify_dwm_hdr_poc_local.py --json     # machine-readable summary
bash scripts/push_when_online.sh                     # finite-retry git push (flaky HTTPS)
```
