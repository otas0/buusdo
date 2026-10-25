"""Linux backend: schedule vkBasalt / vkSumi / Goverlay; Proton prefix ReShade.

Does not implement Vulkan layers or hooks.
"""

from __future__ import annotations

import json
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

_VKBASALT_STATE = ".buusdo/vkbasalt_env.json"


class LinuxBackend(EnhancementBackend):
    def platform_id(self) -> str:
        return HostPlatform.LINUX.value

    def discover_games(self) -> list[EnhancementTarget]:
        games = discover_steam_games(steam_roots(HostPlatform.LINUX))
        return [g.to_target() for g in games]

    def list_capabilities(self, target: EnhancementTarget) -> list[Capability]:
        is_proton = bool(target.metadata.get("proton_prefix") or target.metadata.get("runtime") == "proton")
        return [
            Capability(
                id="vkbasalt",
                title="Vulkan 后处理调度（vkBasalt / vkSumi）",
                description="通过环境变量与 Steam launch options 调度已有 Vulkan 后处理层。",
                available=not is_proton,
                notes="后处理效果为近似增强时须在 UI 标注「近似」。",
            ),
            Capability(
                id="goverlay",
                title="Goverlay 入口",
                description="可选：通过 Goverlay GUI 包装器配置后处理层。",
                available=not is_proton,
            ),
            Capability(
                id="proton_reshade",
                title="Proton 前缀 ReShade 部署",
                description=(
                    "对 Proton 运行的 Windows 游戏，将 ReShade 部署到游戏目录"
                    "（steamapps/common），供 Proton 加载；不是宿主原生注入。"
                ),
                available=is_proton or self._looks_like_windows_game(target),
            ),
        ]

    def install(self, target: EnhancementTarget, options: dict[str, Any] | None = None) -> InstallResult:
        # Same refuse-on-presence semantics under Proton (C1).
        anticheat_guard.check(target, HostPlatform.LINUX)
        options = options or {}
        mode = str(options.get("mode") or self._default_mode(target))

        if mode == "reshade":
            return self._install_reshade(target, options)
        if mode == "vkbasalt":
            return self._install_vkbasalt(target, options)
        raise BuusdoError(f"Unknown Linux install mode: {mode}")

    def uninstall(self, target: EnhancementTarget) -> InstallResult:
        anticheat_guard.check(target, HostPlatform.LINUX)
        details: dict[str, Any] = {}
        with Transaction() as tx:
            reshade_result = reshade.uninstall(tx, target.install_path)
            details["reshade"] = reshade_result
            env_path = target.install_path / _VKBASALT_STATE
            if env_path.is_file():
                tx.delete(env_path)
                details["vkbasalt"] = {"removed": True}
        return InstallResult(
            success=True,
            message="已移除 Linux 增强部署（ReShade / vkBasalt 状态）。",
            details=details,
        )

    def status(self, target: EnhancementTarget) -> dict[str, Any]:
        info = reshade.status(target.install_path)
        env_path = target.install_path / _VKBASALT_STATE
        info["platform"] = self.platform_id()
        info["proton_prefix"] = target.metadata.get("proton_prefix")
        info["vkbasalt_configured"] = env_path.is_file()
        return info

    def _default_mode(self, target: EnhancementTarget) -> str:
        if target.metadata.get("runtime") == "proton" or target.metadata.get("proton_prefix"):
            return "reshade"
        if self._looks_like_windows_game(target):
            return "reshade"
        return "vkbasalt"

    def _looks_like_windows_game(self, target: EnhancementTarget) -> bool:
        exe = target.executable
        if exe and exe.suffix.lower() == ".exe":
            return True
        try:
            return any(p.suffix.lower() == ".exe" for p in target.install_path.iterdir() if p.is_file())
        except OSError:
            return False

    def _install_reshade(self, target: EnhancementTarget, options: dict[str, Any]) -> InstallResult:
        # Deploy next to the Windows game EXE under steamapps/common (Proton loads that tree).
        # Do not write into the Wine prefix drive_c — that is not the Steam game path.
        kit_path = options.get("reshade_kit") or get_reshade_kit_path()
        if not kit_path:
            raise BuusdoError(
                "未配置 ReShade 工具包路径。请传入 reshade_kit 或先 set_reshade_kit_path()。"
            )
        api = None
        if options.get("api"):
            try:
                api = GraphicsApi(str(options["api"]).lower())
            except ValueError as exc:
                raise BuusdoError(f"Unknown graphics API: {options['api']}") from exc

        kit = reshade.resolve_kit(Path(kit_path))
        plan = reshade.plan_deploy(
            target.install_path,
            kit,
            executable=target.executable,
            api=api,
        )
        prefix = target.metadata.get("proton_prefix")
        with Transaction() as tx:
            state = reshade.deploy(tx, plan, target_name=target.name)
            if prefix:
                meta_path = target.install_path / ".buusdo" / "proton.json"
                tx.ensure_dir(meta_path.parent)
                tx.write_text(
                    meta_path,
                    json.dumps(
                        {
                            "proton_prefix": prefix,
                            "app_id": target.metadata.get("app_id"),
                            "note": (
                                "ReShade DLLs are in steamapps/common (game dir), "
                                "not inside the Proton prefix."
                            ),
                        },
                        indent=2,
                    )
                    + "\n",
                )
        return InstallResult(
            success=True,
            message=(
                f"已在 Proton 游戏目录部署 ReShade（{plan.proxy_dll_name}，"
                f"API：{plan.api.value}）。"
            ),
            details=state,
        )

    def _install_vkbasalt(self, target: EnhancementTarget, options: dict[str, Any]) -> InstallResult:
        # Schedule existing vkBasalt via env file the user can paste into Steam launch options.
        enable = options.get("ENABLE_VKBASALT", "1")
        conf = options.get("VKBASALT_CONFIG_FILE", "")
        env = {
            "ENABLE_VKBASALT": str(enable),
            "SteamLaunchHint": "%command%",
        }
        if conf:
            env["VKBASALT_CONFIG_FILE"] = str(conf)
        launch = "ENABLE_VKBASALT=1 %command%"
        if conf:
            launch = f"ENABLE_VKBASALT=1 VKBASALT_CONFIG_FILE={conf} %command%"

        path = target.install_path / _VKBASALT_STATE
        with Transaction() as tx:
            tx.ensure_dir(path.parent)
            tx.write_text(
                path,
                json.dumps(
                    {
                        "target": target.name,
                        "env": env,
                        "steam_launch_options": launch,
                        "note": "近似后处理：由系统已安装的 vkBasalt/vkSumi 层执行，buusdo 只写调度配置。",
                    },
                    indent=2,
                    ensure_ascii=False,
                )
                + "\n",
            )
        return InstallResult(
            success=True,
            message="已写入 vkBasalt 调度配置（近似后处理）。请将 Steam 启动项设为记录中的 launch options。",
            details={"path": str(path), "steam_launch_options": launch},
        )
