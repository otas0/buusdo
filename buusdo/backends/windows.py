"""Windows backend: ReShade / DLSS-via-addon scheduling, RTX Remix mod management.

Does not implement rendering or rebuild path-traced scenes.
"""

from __future__ import annotations

import json
from typing import Any

from buusdo.core import anticheat_guard
from buusdo.core.backend import (
    Capability,
    EnhancementBackend,
    EnhancementTarget,
    InstallResult,
)
from buusdo.core.platform_detect import HostPlatform
from buusdo.core.transaction import Transaction


class WindowsBackend(EnhancementBackend):
    def platform_id(self) -> str:
        return HostPlatform.WINDOWS.value

    def list_capabilities(self, target: EnhancementTarget) -> list[Capability]:
        return [
            Capability(
                id="reshade",
                title="ReShade 后处理调度",
                description="部署 ReShade 作为后处理注入底座（D3D / OpenGL / Vulkan）。",
                available=True,
            ),
            Capability(
                id="dlss5",
                title="神经画质增强（DLSS 5）",
                description=(
                    "通过 ReShade 附加组件或 OptiScaler 分支调度神经画质增强。"
                    "与路径追踪（RTX Remix mod）是不同能力。"
                ),
                available=True,
            ),
            Capability(
                id="rtx_remix_manage",
                title="RTX Remix mod 管理",
                description="仅管理已有的 RTX Remix 路径追踪 mod，不重建场景。",
                available=True,
                notes="不得表述为「已开启光线追踪」。",
            ),
            Capability(
                id="dwm_hdr",
                title="DWM SDR→HDR 色彩兜底",
                description="可选模块；Phase 3 才实现。",
                available=False,
                notes="Phase 3",
            ),
        ]

    def install(self, target: EnhancementTarget, options: dict[str, Any] | None = None) -> InstallResult:
        anticheat_guard.check(target, HostPlatform.WINDOWS)
        options = options or {}
        marker = target.install_path / ".buusdo" / "windows_install.json"
        with Transaction() as tx:
            tx.ensure_dir(marker.parent)
            # Phase 1 scaffold: record intent; ReShade/OptiScaler deploy comes next.
            tx.write_text(
                marker,
                json.dumps({"target": target.name, "options": options}, indent=2) + "\n",
            )
        return InstallResult(
            success=True,
            message="Windows enhancement plan recorded (scaffold).",
            details={"marker": str(marker)},
        )

    def uninstall(self, target: EnhancementTarget) -> InstallResult:
        anticheat_guard.check(target, HostPlatform.WINDOWS)
        marker = target.install_path / ".buusdo" / "windows_install.json"
        with Transaction() as tx:
            if marker.exists():
                tx.delete(marker)
        return InstallResult(success=True, message="Windows enhancement marker removed.")

    def status(self, target: EnhancementTarget) -> dict[str, Any]:
        marker = target.install_path / ".buusdo" / "windows_install.json"
        return {
            "platform": self.platform_id(),
            "installed": marker.exists(),
            "marker": str(marker) if marker.exists() else None,
        }
