"""Helpers for LaunchAgent watch-ci-billing log append checks (no Actions poll)."""

from __future__ import annotations

import re

_TS = re.compile(r"^---- 20\d{2}-\d{2}-\d{2}T")
_EXIT = re.compile(r"^---- exit \d+ ----\s*$")


def exit_follows_latest_timestamp(log_text: str) -> tuple[bool, str]:
    """Require ``---- exit N ----`` after the latest timestamp marker line.

    Returns ``(ok, reason)``. Empty / missing timestamp fails.
    """
    lines = log_text.splitlines()
    last_ts = -1
    for i, line in enumerate(lines):
        if _TS.match(line):
            last_ts = i
    if last_ts < 0:
        return False, "missing ---- timestamp marker"
    for line in lines[last_ts + 1 :]:
        if _EXIT.match(line):
            return True, "ok"
        if _TS.match(line):
            return False, "new timestamp before exit marker"
    return False, "exit marker missing after latest timestamp"


def appended_chunk_ok(full_text: str, before_nbytes: int) -> tuple[bool, str]:
    """Validate growth + exit-after-latest-timestamp on the full log (post-kickstart)."""
    raw = full_text.encode("utf-8", errors="replace")
    if before_nbytes < 0:
        before_nbytes = 0
    if len(raw) <= before_nbytes:
        return False, "log size did not grow"
    return exit_follows_latest_timestamp(full_text)
