"""Linux backend: vkBasalt scheduling + Proton ReShade (incl. Vulkan layer)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from buusdo.core import anticheat_guard, history, preflight, reshade
from buusdo.core.backend import (
    Capability,
    EnhancementBackend,
    EnhancementTarget,
    InstallResult,
)
from buusdo.core.config_store import get_reshade_kit_path, load_game_config, update_game_config
from buusdo.core.discovery import discover_steam_games, list_executable_candidates
from buusdo.core.errors import BuusdoError
from buusdo.core.graphics_detect import GraphicsApi, detect_graphics_api
from buusdo.core.platform_detect import HostPlatform, steam_roots
from buusdo.core.steam_launch import find_localconfig, set_launch_options
from buusdo.core.transaction import Transaction

_VKBASALT_STATE = ".buusdo/vkbasalt_env.json"


class LinuxBackend(EnhancementBackend):
    def platform_id(self) -> str:
        return HostPlatform.LINUX.value

    def discover_games(self) -> list[EnhancementTarget]:
        games = discover_steam_games(steam_roots(HostPlatform.LINUX))
        out: list[EnhancementTarget] = []
        for g in games:
            t = g.to_target()
            cfg = load_game_config(g.app_id)
            if cfg.get("executable"):
                p = Path(cfg["executable"])
                if p.is_file():
                    t = EnhancementTarget(
                        name=t.name,
                        install_path=t.install_path,
                        executable=p,
                        metadata={**t.metadata, "graphics_api": cfg.get("graphics_api")},
                    )
            out.append(t)
        return out

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
                id="proton_reshade",
                title="Proton ReShade 部署",
                description="将 ReShade（含 Vulkan 显式层）部署到 steamapps/common 游戏目录。",
                available=is_proton or self._looks_like_windows_game(target),
            ),
        ]

    def install(self, target: EnhancementTarget, options: dict[str, Any] | None = None) -> InstallResult:
        anticheat_guard.check(target, HostPlatform.LINUX)
        options = options or {}
        mode = str(options.get("mode") or self._default_mode(target))
        target = self._apply_options(target, options)
        try:
            if mode == "reshade":
                result = self._install_reshade(target, options)
            elif mode == "vkbasalt":
                result = self._install_vkbasalt(target, options)
            else:
                raise BuusdoError(f"Unknown Linux install mode: {mode}")
        except Exception as exc:
            history.append_event(f"install:{mode}", target=target.name, success=False, message=str(exc))
            raise
        history.append_event(
            f"install:{mode}",
            target=target.name,
            success=result.success,
            message=result.message,
            details=result.details,
        )
        return result

    def uninstall(self, target: EnhancementTarget) -> InstallResult:
        anticheat_guard.check(target, HostPlatform.LINUX)
        details: dict[str, Any] = {}
        with Transaction() as tx:
            details["reshade"] = reshade.uninstall(tx, target.install_path)
            env_path = target.install_path / _VKBASALT_STATE
            if env_path.is_file():
                tx.delete(env_path)
                details["vkbasalt"] = {"removed": True}
            app_id = target.metadata.get("app_id")
            if app_id and details.get("vkbasalt"):
                localconfig = find_localconfig(steam_roots(HostPlatform.LINUX))
                if localconfig:
                    details["launch_options"] = set_launch_options(tx, localconfig, str(app_id), "")
        result = InstallResult(success=True, message="已移除 Linux 增强部署。", details=details)
        history.append_event("uninstall", target=target.name, success=True, message=result.message, details=details)
        return result

    def status(self, target: EnhancementTarget) -> dict[str, Any]:
        info = reshade.status(target.install_path)
        env_path = target.install_path / _VKBASALT_STATE
        return {
            "platform": self.platform_id(),
            "reshade": info,
            "installed": info.get("installed") or env_path.is_file(),
            "proton_prefix": target.metadata.get("proton_prefix"),
            "vkbasalt_configured": env_path.is_file(),
            "executables": target.metadata.get("executables")
            or [str(p) for p in list_executable_candidates(target.install_path)],
        }

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

    def _apply_options(self, target: EnhancementTarget, options: dict[str, Any]) -> EnhancementTarget:
        game_id = str(target.metadata.get("app_id") or target.name)
        fields: dict[str, Any] = {}
        exe = target.executable
        if options.get("executable"):
            fields["executable"] = str(options["executable"])
            exe = Path(options["executable"])
        if options.get("api"):
            fields["graphics_api"] = str(options["api"])
        if fields:
            update_game_config(game_id, **fields)
        meta = dict(target.metadata)
        if fields.get("graphics_api"):
            meta["graphics_api"] = fields["graphics_api"]
        return EnhancementTarget(
            name=target.name, install_path=target.install_path, executable=exe, metadata=meta
        )

    def _resolve_api(self, options: dict[str, Any], target: EnhancementTarget) -> GraphicsApi | None:
        raw = options.get("api") or target.metadata.get("graphics_api")
        if raw is None:
            return detect_graphics_api(target.executable) if target.executable else None
        try:
            return GraphicsApi(str(raw).lower())
        except ValueError as exc:
            raise BuusdoError(f"Unknown graphics API: {raw}") from exc

    def _install_reshade(self, target: EnhancementTarget, options: dict[str, Any]) -> InstallResult:
        kit_path = options.get("reshade_kit") or get_reshade_kit_path()
        if not kit_path:
            raise BuusdoError("未配置 ReShade 工具包路径。")
        api = self._resolve_api(options, target)
        report = preflight.check_install_preflight(target, api=api)
        if not report.ok:
            raise BuusdoError("; ".join(i.message for i in report.issues if i.level.value == "error"))
        kit = reshade.resolve_kit(Path(kit_path))
        plan = reshade.plan_deploy(
            target.install_path, kit, executable=target.executable, api=api
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
                            "mode": plan.mode,
                        },
                        indent=2,
                    )
                    + "\n",
                )
            # Vulkan layer: also write Steam launch options when app_id known
            if plan.mode == "vulkan_layer" and target.metadata.get("app_id"):
                hint = (state.get("deployed") or {}).get("steam_launch_hint")
                localconfig = find_localconfig(steam_roots(HostPlatform.LINUX))
                if hint and localconfig:
                    state["launch_options"] = set_launch_options(
                        tx, localconfig, str(target.metadata["app_id"]), hint
                    )
        return InstallResult(
            success=True,
            message=f"已在 Proton 游戏目录部署 ReShade（{plan.mode}，API {plan.api.value}）。",
            details=state,
        )

    def _install_vkbasalt(self, target: EnhancementTarget, options: dict[str, Any]) -> InstallResult:
        conf = options.get("VKBASALT_CONFIG_FILE", "")
        launch = "ENABLE_VKBASALT=1 %command%"
        if conf:
            launch = f"ENABLE_VKBASALT=1 VKBASALT_CONFIG_FILE={conf} %command%"
        path = target.install_path / _VKBASALT_STATE
        details: dict[str, Any] = {}
        with Transaction() as tx:
            tx.ensure_dir(path.parent)
            tx.write_text(
                path,
                json.dumps(
                    {
                        "target": target.name,
                        "steam_launch_options": launch,
                        "note": "近似后处理：由系统已安装的 vkBasalt/vkSumi 层执行。",
                    },
                    indent=2,
                    ensure_ascii=False,
                )
                + "\n",
            )
            app_id = target.metadata.get("app_id")
            write_steam = options.get("write_steam_launch", True)
            if write_steam and app_id:
                localconfig = find_localconfig(steam_roots(HostPlatform.LINUX))
                if localconfig is None:
                    raise BuusdoError("未找到 Steam localconfig.vdf，无法写回启动项。")
                details["launch_options"] = set_launch_options(
                    tx, localconfig, str(app_id), launch
                )
        details["path"] = str(path)
        details["steam_launch_options"] = launch
        return InstallResult(
            success=True,
            message="已写入 vkBasalt 调度配置（近似后处理），并尝试写回 Steam 启动项。",
            details=details,
        )
