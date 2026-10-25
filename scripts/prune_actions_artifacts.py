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
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any

DEFAULT_REPOS = (
    "otas0/buusdo",
    "otas0/Zintriq",
)


def _gh_api(path: str) -> Any:
    proc = subprocess.run(
        ["gh", "api", path],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or f"gh api failed: {path}")
    return json.loads(proc.stdout) if proc.stdout.strip() else {}


def _gh_delete(path: str) -> None:
    proc = subprocess.run(
        ["gh", "api", "-X", "DELETE", path],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or f"delete failed: {path}")


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
