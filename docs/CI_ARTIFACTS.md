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

1. Re-run CI on `main` / `phase3/dwm-hdr`.
2. Download `dwm-hdr-poc` and confirm `hlsl_sources.zip` + `manifest.json` → `hlsl_sha256`.
