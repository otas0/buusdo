#!/usr/bin/env bash
# Store current `gh` token as repo secret ARTIFACT_PRUNE_TOKEN so the weekly
# prune-artifacts workflow can delete sibling-repo (e.g. Zintriq) artifacts.
#
# Requires: gh auth with repo admin on otas0/buusdo + read access to otas0/Zintriq.
set -euo pipefail

REPO="${1:-otas0/buusdo}"
TOKEN="$(gh auth token)"
if [[ -z "${TOKEN}" ]]; then
  echo "gh auth token failed — run: gh auth login -s repo,workflow,admin:repo_hook" >&2
  exit 1
fi

# Smoke: token can list Zintriq artifacts (cross-repo prune target).
HTTP="$(curl -sS -o /tmp/buusdo-prune-token-check.json -w '%{http_code}' \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/otas0/Zintriq/actions/artifacts?per_page=1" || true)"
if [[ "${HTTP}" != "200" ]]; then
  echo "WARN: Zintriq artifacts API returned HTTP ${HTTP} — token may lack access." >&2
  echo "      Weekly job will still prune ${REPO} via GITHUB_TOKEN fallback." >&2
else
  echo "Zintriq artifact list OK (HTTP 200)."
fi

printf '%s' "${TOKEN}" | gh secret set ARTIFACT_PRUNE_TOKEN -R "${REPO}"
echo "Set ${REPO} secret ARTIFACT_PRUNE_TOKEN."
gh secret list -R "${REPO}" | grep -E 'ARTIFACT_PRUNE_TOKEN|^NAME' || true
echo "Tip: Actions → prune-artifacts → Run workflow to verify."
