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

## Stabilizing `gh` Actions API (avoid Forbidden)

Intermittent `Forbidden` on `repos/*/actions/*` is usually auth/account context, not ACL:

1. Prefer a single active login: `gh auth status` (expect `repo` + `workflow` scopes).
2. If you use multiple accounts: `gh auth switch` to the org owner that can manage Actions.
3. Retry listing with: `gh api repos/otas0/buusdo/actions/artifacts` — HTTP 200 means OK.
4. Avoid sandboxed shells that block GitHub HTTPS CONNECT (shows up as 502 / Forbidden).
5. For CI triggers without push: `gh workflow run ci.yml --ref main` (requires `workflow_dispatch`).
