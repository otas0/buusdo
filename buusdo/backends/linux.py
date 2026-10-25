"""Linux backend: schedule vkBasalt / vkSumi / Goverlay; Proton prefix reuse.

Does not implement Vulkan layers or hooks.
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


class LinuxBackend(EnhancementBackend):
    def platform_id(self) -> str:
        return HostPlatform.LINUX.value

    def list_capabilities(self, target: EnhancementTarget) -> list[Capability]:
        return [
            Capability(
                id="vkbasalt",
                title="Vulkan 后处理调度（vkBasalt / vkSumi）",
                description="通过环境变量与 Steam launch options 调度已有 Vulkan 后处理层。",
                available=True,
                notes="后处理效果为近似增强时须在 UI 标注「近似」。",
            ),
            Capability(
                id="goverlay",
                title="Goverlay 入口",
                description="可选：通过 Goverlay GUI 包装器配置后处理层。",
                available=True,
            ),
            Capability(
                id="proton_reshade",
                title="Proton 前缀 ReShade 部署",
                description=(
                    "对 Proton 运行的 Windows 游戏，将 ReShade 部署到 Proton prefix，"
                    "而非宿主文件系统。"
                ),
                available=True,
            ),
        ]

    def install(self, target: EnhancementTarget, options: dict[str, Any] | None = None) -> InstallResult:
        # Same refuse-on-presence semantics under Proton (C1).
        anticheat_guard.check(target, HostPlatform.LINUX)
        options = options or {}
        marker = target.install_path / ".buusdo" / "linux_install.json"
        with Transaction() as tx:
            tx.ensure_dir(marker.parent)
            tx.write_text(
                marker,
                json.dumps({"target": target.name, "options": options}, indent=2) + "\n",
            )
        return InstallResult(
            success=True,
            message="Linux enhancement plan recorded (scaffold).",
            details={"marker": str(marker)},
        )

    def uninstall(self, target: EnhancementTarget) -> InstallResult:
        anticheat_guard.check(target, HostPlatform.LINUX)
        marker = target.install_path / ".buusdo" / "linux_install.json"
        with Transaction() as tx:
            if marker.exists():
                tx.delete(marker)
        return InstallResult(success=True, message="Linux enhancement marker removed.")

    def status(self, target: EnhancementTarget) -> dict[str, Any]:
        marker = target.install_path / ".buusdo" / "linux_install.json"
        return {
            "platform": self.platform_id(),
            "installed": marker.exists(),
            "marker": str(marker) if marker.exists() else None,
        }
