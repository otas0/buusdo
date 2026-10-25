"""Install preflight checks. Warnings only for conflicts; anticheat remains hard-block (C1)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from buusdo.core.backend import EnhancementTarget
from buusdo.core.graphics_detect import RESHADE_PROXY_DLL, GraphicsApi


class PreflightLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"  # blocks install (non-anticheat hard failures)


@dataclass
class PreflightIssue:
    level: PreflightLevel
    code: str
    message: str


@dataclass
class PreflightReport:
    issues: list[PreflightIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(i.level is PreflightLevel.ERROR for i in self.issues)

    def add(self, level: PreflightLevel, code: str, message: str) -> None:
        self.issues.append(PreflightIssue(level=level, code=code, message=message))


def check_install_preflight(
    target: EnhancementTarget,
    *,
    api: GraphicsApi | None = None,
    proxy_name: str | None = None,
) -> PreflightReport:
    report = PreflightReport()
    root = target.install_path

    if not root.exists():
        report.add(PreflightLevel.ERROR, "missing_install", f"安装目录不存在：{root}")
        return report

    if not os.access(root, os.W_OK):
        report.add(PreflightLevel.ERROR, "not_writable", f"安装目录不可写：{root}")

    # Read-only Steam library heuristic
    try:
        probe = root / ".buusdo_write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
    except OSError:
        report.add(PreflightLevel.ERROR, "readonly_library", "疑似只读游戏库，无法写入增强文件")

    resolved_proxy = proxy_name
    if resolved_proxy is None and api is not None:
        resolved_proxy = RESHADE_PROXY_DLL.get(api) or None
    if resolved_proxy is None:
        resolved_proxy = "dxgi.dll"

    existing = root / resolved_proxy
    if existing.is_file():
        report.add(
            PreflightLevel.WARNING,
            "proxy_conflict",
            f"已存在 {resolved_proxy}；部署将覆盖并在卸载时逐字节恢复原文",
        )

    for name in ("d3d9.dll", "dxgi.dll", "opengl32.dll", "d3d11.dll"):
        p = root / name
        if p.is_file() and name != resolved_proxy:
            report.add(
                PreflightLevel.INFO,
                "other_proxy_present",
                f"目录中另有 {name}（可能来自其他注入工具）",
            )

    return report
