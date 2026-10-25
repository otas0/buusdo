"""Windows backend: ReShade / DLSS-via-addon scheduling, RTX Remix mod management.

Does not implement rendering or rebuild path-traced scenes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from buusdo.core import anticheat_guard, reshade
from buusdo.core.backend import (
    Capability,
    EnhancementBackend,
    EnhancementTarget,
    InstallResult,
)
from buusdo.core.config_store import get_reshade_kit_path
from buusdo.core.discovery import discover_steam_games
from buusdo.core.errors import BuusdoError
from buusdo.core.graphics_detect import GraphicsApi
from buusdo.core.platform_detect import HostPlatform, steam_roots
from buusdo.core.transaction import Transaction


class WindowsBackend(EnhancementBackend):
    def platform_id(self) -> str:
        return HostPlatform.WINDOWS.value

    def discover_games(self) -> list[EnhancementTarget]:
        games = discover_steam_games(steam_roots(HostPlatform.WINDOWS))
        return [g.to_target() for g in games]

    def list_capabilities(self, target: EnhancementTarget) -> list[Capability]:
        return [
            Capability(
                id="reshade",
                title="ReShade 后处理调度",
                description="部署 ReShade 作为后处理注入底座（D3D / OpenGL）。",
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
        kit_path = self._resolve_kit(options)
        api = self._resolve_api(options)
        kit = reshade.resolve_kit(kit_path)
        plan = reshade.plan_deploy(
            target.install_path,
            kit,
            executable=target.executable,
            api=api,
        )
        with Transaction() as tx:
            state = reshade.deploy(tx, plan, target_name=target.name)
        return InstallResult(
            success=True,
            message=(
                f"已部署 ReShade 后处理底座（代理 {plan.proxy_dll_name}，"
                f"检测 API：{plan.api.value}）。"
            ),
            details=state,
        )

    def uninstall(self, target: EnhancementTarget) -> InstallResult:
        anticheat_guard.check(target, HostPlatform.WINDOWS)
        with Transaction() as tx:
            result = reshade.uninstall(tx, target.install_path)
        if not result.get("removed"):
            return InstallResult(success=True, message="未发现 ReShade 部署状态。", details=result)
        return InstallResult(
            success=True,
            message="已卸载 ReShade，并按事务回滚恢复被覆盖文件。",
            details=result,
        )

    def status(self, target: EnhancementTarget) -> dict[str, Any]:
        info = reshade.status(target.install_path)
        info["platform"] = self.platform_id()
        return info

    def _resolve_kit(self, options: dict[str, Any]) -> Path:
        raw = options.get("reshade_kit") or get_reshade_kit_path()
        if not raw:
            raise BuusdoError(
                "未配置 ReShade 工具包路径。请在选项中传入 reshade_kit，"
                "或先调用 set_reshade_kit_path()。"
            )
        return Path(raw)

    def _resolve_api(self, options: dict[str, Any]) -> GraphicsApi | None:
        raw = options.get("api")
        if raw is None:
            return None
        try:
            return GraphicsApi(str(raw).lower())
        except ValueError as exc:
            raise BuusdoError(f"Unknown graphics API: {raw}") from exc
