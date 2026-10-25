# CI artifacts, quota, and `continue-on-error`

## What we upload

| Artifact | Job | When | Retention |
|----------|-----|------|-----------|
| `dwm-hdr-poc` | `dwm-hdr-poc` | HLSL present (always after compile attempt) | 3 days |
| `dwm-hdr-hlsl-sources` | `dwm-hdr-poc` | HLSL present | 3 days |
| `qt-diag-macos` | `devui-macos` | smoke failure | default |
| `qt-plugin-dirs-macos` | `devui-macos` | smoke failure | default |

`dwm-hdr-poc` includes `manifest.json`, optional `.cso`, and (on `skipped_no_compiler` / `compile_failed`) `hlsl_sources/` + `hlsl_sources.zip`.

## Artifact storage quota

GitHub Actions artifact storage is billed/capped **per account/org**, not per repo.
If upload fails with:

```text
Failed to CreateArtifact: Artifact storage quota has been hit
```

free space by deleting old artifacts (GitHub → repo → Actions → Artifacts, or
`gh api -X DELETE repos/<owner>/<repo>/actions/artifacts/<id>`), then re-run the workflow.

Quota recalculation can take 6–12 hours after deletes.

## Why upload steps use `continue-on-error: true`

Compile/test results must remain authoritative. A full artifact-store quota must **not**
mark `dwm-hdr-poc` or `devui-macos` failed when the real work already succeeded.
Upload steps therefore set:

```yaml
continue-on-error: true
```

Job-level `continue-on-error` for `dwm-hdr-poc` stays **`false`**: a real compile
failure (when Windows Kits / fxc / dxc are present) still fails the job.

## After quota recovers

1. Re-run CI on `main` / `phase3/dwm-hdr` (push, or **Actions → ci → Run workflow** via `workflow_dispatch`).
2. Download `dwm-hdr-poc` and confirm `hlsl_sources.zip` + `manifest.json` → `hlsl_sha256`.
3. Offline check without waiting for uploads:

```bash
python scripts/compile_dwm_hdr_poc.py --out /tmp/buusdo-dwm-hdr-poc
python -c "import json,zipfile; from pathlib import Path; r=Path('/tmp/buusdo-dwm-hdr-poc'); print(json.loads((r/'manifest.json').read_text())['hlsl_sha256']); print(zipfile.ZipFile(r/'hlsl_sources.zip').namelist())"
```

## Prune sibling-repo artifacts (quota hygiene)

Do **not** let other otas0 repos (especially Zintriq desktop logs) fill the shared Actions storage:

```bash
python scripts/prune_actions_artifacts.py --list
python scripts/prune_actions_artifacts.py --delete --older-than-days 3 --yes
```

Scheduled workflow: `.github/workflows/prune-artifacts.yml` (weekly Monday + `workflow_dispatch`).
Set repo secret `ARTIFACT_PRUNE_TOKEN` (classic PAT with `repo` + access to Zintriq) so the job can prune siblings; otherwise it still prunes `otas0/buusdo` via `GITHUB_TOKEN`.

```bash
# One-shot: store current gh token as the secret (needs admin on buusdo)
bash scripts/setup_artifact_prune_token.sh otas0/buusdo
```

## Billing / spending limit (0s empty-step fails)

API cannot raise the spending limit for this account (`/users/.../settings/billing/actions` → 404).
Only a human can fix it in the browser: **https://github.com/settings/billing** → Spending limits / payment method.
Until runners start, `workflow_dispatch` returns 204 but jobs die in ~3s with `steps=[]` and Artifacts stay 0.
CI `run-name` + each job's first step write this tip into the Actions summary when runners *do* start.
`scripts/watch_ci_billing.py` (and the hourly LaunchAgent) exit 1 / notify when the newest run looks blocked.
Local `python scripts/prune_actions_artifacts.py --list` still works without runners; the `prune-artifacts` workflow needs billing fixed too.

After spending limit is fixed: trigger **one** `workflow_dispatch` (or push) and stop — do not agent-poll CI.
Offline PoC check (no Actions needed): `python scripts/verify_dwm_hdr_poc_local.py`.

Local detector (bell + optional macOS notification):

```bash
python scripts/watch_ci_billing.py --notify --once
# exit 1 when the newest main run looks billing-blocked

# Hourly LaunchAgent (macOS):
bash scripts/install_watch_ci_billing_launchd.sh
```

## Stabilizing `gh` Actions API (avoid Forbidden)

Intermittent `Forbidden` on `repos/*/actions/*` is often the **`gh` CLI transport**, not missing scopes.
`scripts/prune_actions_artifacts.py` now calls the REST API with a Bearer token via `urllib`
(`GH_TOKEN` / `gh auth token`) — prefer that script over raw `gh api` for artifact hygiene.

1. Prefer a single active login: `gh auth status` (expect `repo` + `workflow` scopes).
2. If you use multiple accounts: `gh auth switch` to the org owner that can manage Actions.
3. Verify with curl (more reliable than `gh api` when the CLI returns Forbidden):

```bash
TOKEN=$(gh auth token)
curl -sS -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/otas0/buusdo/actions/artifacts"
```

4. Avoid sandboxed shells that block GitHub HTTPS CONNECT (shows up as 502 / Forbidden).
5. For CI triggers without push: **Actions → ci → Run workflow** or:

```bash
TOKEN=$(gh auth token)
curl -sS -X POST -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/otas0/buusdo/actions/workflows/ci.yml/dispatches" \
  -d '{"ref":"main","inputs":{"reason":"manual"}}'
```

6. If jobs die in ~2–4s with *“recent account payments have failed or your spending limit needs to be increased”*, fix **Billing & plans / spending limit** first — no artifact will upload until runners can start.
7. Prefer `GH_TOKEN=$(gh auth token)` in scripts; do not rely on bare `gh api` inside automation.

## Offline PoC verify (no Actions / no network)

Prefer the wrapper (compiles/materializes, then checks zip + `hlsl_sha256`):

```bash
python scripts/verify_dwm_hdr_poc_local.py
python scripts/verify_dwm_hdr_poc_local.py --json   # machine-readable summary
# expect ok=true, status=skipped_no_compiler on macOS without fxc/dxc
```

Equivalent manual steps:

```bash
python scripts/compile_dwm_hdr_poc.py --out /tmp/buusdo-dwm-hdr-poc
python -c "import json,zipfile; from pathlib import Path; r=Path('/tmp/buusdo-dwm-hdr-poc'); print(json.loads((r/'manifest.json').read_text())['hlsl_sha256']); print(zipfile.ZipFile(r/'hlsl_sources.zip').namelist())"
```

## Agent / automation policy

- **Do not** agent-poll GitHub Actions for green builds or artifacts.
- Billing/spending-limit recovery is human-only; after fix, **one** `workflow_dispatch` (or push) is enough.
- Local awareness of 0-step failures: macOS LaunchAgent via `scripts/install_watch_ci_billing_launchd.sh` only (appending logs). Do **not** agent-poll Actions.
- After Billing is fixed by a human: **one** `workflow_dispatch` (or push), then stop.
- Verify LaunchAgent append markers: `bash scripts/assert_watch_ci_billing_log_append.sh`
- Flaky `git push` HTTPS: `bash scripts/push_when_online.sh` (finite retries).

## Current status (checked offline)

- Actions Artifacts for `otas0/buusdo`: often **0** while spending limit blocks runners or uploads.
- Use offline PoC verify above instead of waiting on `dwm-hdr-poc` uploads.
