#!/usr/bin/env python3
"""Detect GitHub Actions runs that die with empty steps (billing / spending limit).

Typical symptom: every job concludes in ~2–4s with ``steps=[]`` and no checkout.
This script polls recent runs and prints a local alert (bell + optional macOS banner).

Examples:
  python scripts/watch_ci_billing.py
  python scripts/watch_ci_billing.py --repo otas0/buusdo --limit 5 --notify
  python scripts/watch_ci_billing.py --once   # exit 1 if latest looks billing-blocked
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

API = "https://api.github.com"
DEFAULT_REPO = "otas0/buusdo"
BILLING_URL = "https://github.com/settings/billing"
# Jobs that never start usually finish within a few seconds.
EMPTY_STEP_MAX_DURATION_S = 15.0


def _token() -> str:
    env = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if env:
        return env.strip()
    proc = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True)
    if proc.returncode != 0 or not proc.stdout.strip():
        raise RuntimeError("Need GH_TOKEN / GITHUB_TOKEN or `gh auth token`")
    return proc.stdout.strip()


def _get(path: str) -> Any:
    url = path if path.startswith("http") else f"{API}/{path.lstrip('/')}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {_token()}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "buusdo-watch-ci-billing",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:400]
        raise RuntimeError(f"GET {url} -> HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"GET {url} -> network error: {exc}") from exc


def _parse_ts(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def _job_duration_s(job: dict[str, Any]) -> float | None:
    start = _parse_ts(job.get("started_at"))
    end = _parse_ts(job.get("completed_at"))
    if not start or not end:
        return None
    return max(0.0, (end - start).total_seconds())


def classify_run(repo: str, run_id: int) -> dict[str, Any]:
    """Return billing-block heuristics for one workflow run."""
    data = _get(f"repos/{repo}/actions/runs/{run_id}/jobs?per_page=100")
    jobs = list(data.get("jobs") or [])
    empty = 0
    fast = 0
    for job in jobs:
        steps = job.get("steps") or []
        if len(steps) == 0:
            empty += 1
        dur = _job_duration_s(job)
        if dur is not None and dur <= EMPTY_STEP_MAX_DURATION_S:
            fast += 1
    blocked = bool(jobs) and empty == len(jobs) and fast == len(jobs)
    return {
        "run_id": run_id,
        "jobs": len(jobs),
        "empty_step_jobs": empty,
        "fast_jobs": fast,
        "billing_blocked_likely": blocked,
    }


def _notify_local(title: str, body: str) -> None:
    # Terminal bell (always).
    sys.stdout.write("\a")
    sys.stdout.flush()
    if sys.platform == "darwin":
        script = (
            f'display notification {json.dumps(body)} with title {json.dumps(title)}'
        )
        subprocess.run(["osascript", "-e", script], check=False, capture_output=True)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", default=DEFAULT_REPO, help="owner/name")
    p.add_argument("--limit", type=int, default=5, help="Recent runs to inspect")
    p.add_argument(
        "--branch",
        default="main",
        help="Branch filter (empty string = any)",
    )
    p.add_argument(
        "--notify",
        action="store_true",
        help="macOS notification + terminal bell when a blocked run is found",
    )
    p.add_argument(
        "--once",
        action="store_true",
        help="Exit 1 if the newest matching run looks billing-blocked",
    )
    args = p.parse_args(argv)

    q = f"repos/{args.repo}/actions/runs?per_page={max(1, args.limit)}"
    if args.branch:
        q += f"&branch={args.branch}"
    payload = _get(q)
    runs = list(payload.get("workflow_runs") or [])
    if not runs:
        print(f"{args.repo}: no recent runs")
        return 0

    blocked_any = False
    newest_blocked = False
    for i, run in enumerate(runs):
        run_id = int(run["id"])
        info = classify_run(args.repo, run_id)
        flag = "BILLING?" if info["billing_blocked_likely"] else "ok"
        print(
            f"{flag}  run={run_id}  {run.get('conclusion') or run.get('status')}  "
            f"sha={str(run.get('head_sha') or '')[:7]}  "
            f"jobs={info['jobs']} empty_steps={info['empty_step_jobs']}  "
            f"{(run.get('display_title') or run.get('name') or '')[:60]}"
        )
        if info["billing_blocked_likely"]:
            blocked_any = True
            if i == 0:
                newest_blocked = True
            print(
                f"  -> jobs died with steps=[] in ≤{EMPTY_STEP_MAX_DURATION_S:.0f}s. "
                f"Raise Actions spending limit: {BILLING_URL}"
            )

    if blocked_any and args.notify:
        _notify_local(
            "buusdo CI billing",
            f"{args.repo}: 0-step Actions failures — check spending limit",
        )

    if args.once and newest_blocked:
        return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from exc
