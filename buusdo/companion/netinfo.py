"""LAN address helpers for companion URLs (not in core/ui — C3)."""

from __future__ import annotations

import socket


DEFAULT_PORT = 8765


def primary_lan_ipv4() -> str:
    """Best-effort LAN IPv4; falls back to 127.0.0.1 (never raises)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            host = sock.getsockname()[0]
            if host and not host.startswith("127."):
                return host
    except OSError:
        pass
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            ip = info[4][0]
            if ip and not ip.startswith("127."):
                return ip
    except OSError:
        pass
    return "127.0.0.1"


def companion_base_url(*, host: str | None = None, port: int = DEFAULT_PORT) -> str:
    h = host or primary_lan_ipv4()
    return f"http://{h}:{int(port)}"


def companion_bind_addr(*, loopback_only: bool, port: int) -> str:
    """Display bind as ``host:port`` (loopback or primary LAN IPv4)."""
    host = "127.0.0.1" if loopback_only else primary_lan_ipv4()
    p = int(port or 0)
    return f"{host}:{p}" if p else host


def truncate_bind_addr(addr: str, *, max_len: int = 22) -> str:
    """Short chip label; keep ``:port`` visible when possible."""
    if max_len < 6 or len(addr) <= max_len:
        return addr
    if ":" in addr:
        host, _, port = addr.rpartition(":")
        budget = max_len - len(port) - 2  # ellipsis + colon
        if budget >= 4 and host:
            return f"{host[:budget]}…:{port}"
    return addr[: max_len - 1] + "…"
