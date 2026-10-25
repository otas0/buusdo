#!/usr/bin/env python3
"""List / prune GitHub Actions artifacts to avoid org-wide storage quota blowups.

Default watch list includes buusdo + sibling repos known to accumulate desktop logs
(e.g. Zintriq). Requires `gh` authenticated with `repo` + `workflow` scopes.

Examples:
  python scripts/prune_actions_artifacts.py --list
  python scripts/prune_actions_artifacts.py --delete --older-than-days 3 --yes
  python scripts/prune_actions_artifacts.py --repos otas0/buusdo,otas0/Zintriq --list
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any

DEFAULT_REPOS = (
    "otas0/buusdo",
    "otas0/Zintriq",
)
API = "https://api.github.com"


def _token() -> str:
    env = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if env:
        return env.strip()
    proc = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True)
    if proc.returncode != 0 or not proc.stdout.strip():
        raise RuntimeError(
            "No GH_TOKEN/GITHUB_TOKEN and `gh auth token` failed. "
            "Run: gh auth login -s repo,workflow"
        )
    return proc.stdout.strip()


def _request(method: str, path: str) -> Any:
    """Call GitHub REST with Bearer token (avoids intermittent `gh api` Forbidden)."""
    url = path if path.startswith("http") else f"{API}/{path.lstrip('/')}"
    req = urllib.request.Request(
        url,
        method=method,
        headers={
            "Authorization": f"Bearer {_token()}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "buusdo-prune-actions-artifacts",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body.strip() else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"{method} {url} -> HTTP {exc.code}: {detail}") from exc


def _gh_api(path: str) -> Any:
    return _request("GET", f"repos/{path}" if not path.startswith("repos/") else path)


def _gh_delete(path: str) -> None:
    _request("DELETE", f"repos/{path}" if not path.startswith("repos/") else path)


def _list_artifacts(repo: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    page = 1
    while True:
        data = _gh_api(f"repos/{repo}/actions/artifacts?per_page=100&page={page}")
        batch = data.get("artifacts") or []
        out.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return out


def _parse_ts(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        text = raw.replace("Z", "+00:00")
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--repos",
        default=",".join(DEFAULT_REPOS),
        help="Comma-separated owner/name repos to inspect",
    )
    p.add_argument("--list", action="store_true", help="List artifacts (default if no --delete)")
    p.add_argument("--delete", action="store_true", help="Delete matching artifacts")
    p.add_argument(
        "--older-than-days",
        type=float,
        default=0,
        help="Only delete artifacts older than N days (0 = all)",
    )
    p.add_argument(
        "--max-bytes",
        type=int,
        default=0,
        help="Only delete artifacts larger than this size (0 = any size)",
    )
    p.add_argument("--yes", action="store_true", help="Required with --delete")
    args = p.parse_args(argv)

    if args.delete and not args.yes:
        print("refusing --delete without --yes", file=sys.stderr)
        return 2
    if not args.delete:
        args.list = True

    now = datetime.now(timezone.utc)
    repos = [r.strip() for r in args.repos.split(",") if r.strip()]
    total = 0
    for repo in repos:
        try:
            arts = _list_artifacts(repo)
        except RuntimeError as exc:
            print(f"{repo}: ERROR {exc}", file=sys.stderr)
            continue
        print(f"## {repo} ({len(arts)} artifacts)")
        for a in arts:
            total += 1
            created = _parse_ts(a.get("created_at"))
            age_days = (now - created).total_seconds() / 86400 if created else None
            size = int(a.get("size_in_bytes") or 0)
            line = (
                f"  {a.get('id')}  {a.get('name')}  "
                f"{size}B  age={age_days:.1f}d" if age_days is not None else
                f"  {a.get('id')}  {a.get('name')}  {size}B"
            )
            print(line)
            if not args.delete:
                continue
            if args.older_than_days and (age_days is None or age_days < args.older_than_days):
                continue
            if args.max_bytes and size < args.max_bytes:
                continue
            try:
                _gh_delete(f"repos/{repo}/actions/artifacts/{a['id']}")
                print(f"    deleted {a['id']}")
            except RuntimeError as exc:
                print(f"    FAIL {a['id']}: {exc}", file=sys.stderr)
    print(f"# scanned {total} artifacts across {len(repos)} repos")
    print("# tip: after deletes, GitHub may take 6–12h to recalculate quota")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
