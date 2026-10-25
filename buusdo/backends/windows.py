"""Windows backend: ReShade / OptiScaler scheduling, RTX Remix mod management."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from buusdo.backends import vulkan_layer_win
from buusdo.core import (
    anticheat_guard,
    conflict,
    display_profile,
    dwm_hdr,
    history,
    optiscaler,
    preflight,
    reshade,
    rtx_remix,
)
from buusdo.core.backend import (
    Capability,
    EnhancementBackend,
    EnhancementTarget,
    InstallResult,
)
from buusdo.core.config_store import (
    get_game_pref,
    get_optiscaler_kit_path,
    get_reshade_kit_path,
    load_game_config,
    update_game_config,
)
from buusdo.core.errors import BuusdoError
from buusdo.core.graphics_detect import GraphicsApi, detect_graphics_api
from buusdo.core.library_cache import load_cached_games
from buusdo.core.discovery import list_executable_candidates
from buusdo.core.platform_detect import HostPlatform, steam_roots
from buusdo.core.transaction import Transaction


class WindowsBackend(EnhancementBackend):
    def platform_id(self) -> str:
        return HostPlatform.WINDOWS.value

    def discover_games(self) -> list[EnhancementTarget]:
        games = load_cached_games(steam_roots(HostPlatform.WINDOWS))
        targets = []
        for g in games:
            t = g.to_target()
            cfg = load_game_config(g.app_id)
            targets.append(self._apply_saved_prefs(t, cfg))
        return targets

    def list_capabilities(self, target: EnhancementTarget) -> list[Capability]:
        remix = rtx_remix.detect(target.install_path)
        return [
            Capability(
                id="reshade",
                title="ReShade 后处理调度",
                description="部署 ReShade（D3D / OpenGL 代理 DLL，或 Vulkan 显式层）。",
                available=True,
            ),
            Capability(
                id="optiscaler",
                title="神经画质增强（OptiScaler / DLSS 附加组件）",
                description=(
                    "与 ReShade 底座解耦；调度本地 OptiScaler/神经超分组件。"
                    "与路径追踪（RTX Remix）是不同能力。"
                ),
                available=True,
            ),
            Capability(
                id="rtx_remix_manage",
                title="RTX Remix mod 管理",
                description="仅管理已有的 RTX Remix 路径追踪 mod，不重建场景。",
                available=bool(remix["present"] or remix["disabled"]),
                notes="不得表述为「已开启光线追踪」。",
            ),
            Capability(
                id="display_profile",
                title="按游戏显示/HDR 配置",
                description="保存并协调每游戏显示偏好（分辨率/刷新率/HDR 偏好）。",
                available=True,
            ),
            Capability(
                id="dwm_hdr",
                title="DWM SDR→HDR 色彩兜底",
                description=dwm_hdr.status()["description"],
                available=dwm_hdr.is_available(),
                notes="Phase 3 — 接口已预留",
            ),
        ]

    def install(self, target: EnhancementTarget, options: dict[str, Any] | None = None) -> InstallResult:
        anticheat_guard.check(target, HostPlatform.WINDOWS)
        options = options or {}
        mode = str(options.get("mode") or "reshade")
        target = self._resolve_target_prefs(target, options)

        try:
            if mode == "reshade":
                result = self._install_reshade(target, options)
            elif mode == "optiscaler":
                result = self._install_optiscaler(target, options)
            elif mode == "rtx_remix_enable":
                result = self._remix_toggle(target, enable=True)
            elif mode == "rtx_remix_disable":
                result = self._remix_toggle(target, enable=False)
            elif mode == "display_profile":
                result = self._apply_display_profile(target, options)
            elif mode == "dwm_hdr":
                dwm_hdr.install()
                raise AssertionError("unreachable")
            else:
                raise BuusdoError(f"Unknown Windows install mode: {mode}")
        except Exception as exc:
            history.append_event(
                f"install:{mode}", target=target.name, success=False, message=str(exc)
            )
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
        anticheat_guard.check(target, HostPlatform.WINDOWS)
        details: dict[str, Any] = {}
        with Transaction() as tx:
            details["reshade"] = reshade.uninstall(tx, target.install_path)
            details["optiscaler"] = optiscaler.uninstall(tx, target.install_path)
            details["vulkan_layer"] = vulkan_layer_win.remove_vk_layer_writeback(
                tx, target.install_path
            )
        result = InstallResult(
            success=True,
            message="已卸载 ReShade / OptiScaler / Vulkan 层写回。",
            details=details,
        )
        history.append_event(
            "uninstall", target=target.name, success=True, message=result.message, details=details
        )
        return result

    def status(self, target: EnhancementTarget) -> dict[str, Any]:
        rs = reshade.status(target.install_path)
        op = optiscaler.status(target.install_path)
        return {
            "platform": self.platform_id(),
            "reshade": rs,
            "optiscaler": op,
            "rtx_remix": rtx_remix.status(target.install_path),
            "dwm_hdr": dwm_hdr.status(target.install_path),
            "installed": rs.get("installed") or op.get("installed"),
            "executables": target.metadata.get("executables")
            or [str(p) for p in list_executable_candidates(target.install_path)],
            "game_config": load_game_config(str(target.metadata.get("app_id") or target.name)),
            "display_profile": (
                display_profile.get_game_profile(
                    str(target.metadata.get("app_id") or target.name)
                )
            ),
        }

    def _install_reshade(self, target: EnhancementTarget, options: dict[str, Any]) -> InstallResult:
        kit_path = options.get("reshade_kit") or get_reshade_kit_path()
        if not kit_path:
            raise BuusdoError("未配置 ReShade 工具包路径。")
        api = self._resolve_api(options, target)
        report = preflight.check_install_preflight(target, api=api)
        if not report.ok:
            raise BuusdoError(
                "; ".join(i.message for i in report.issues if i.level.value == "error")
            )

        kit = reshade.resolve_kit(Path(kit_path))
        plan = reshade.plan_deploy(
            target.install_path, kit, executable=target.executable, api=api
        )
        conflicts = conflict.check_install_conflicts(
            target, mode="reshade", reshade_proxy=plan.proxy_dll_name
        )
        if conflicts.blocked:
            raise BuusdoError("; ".join(i.message for i in conflicts.issues if i.severity.value == "block"))

        with Transaction() as tx:
            state = reshade.deploy(tx, plan, target_name=target.name)
            if plan.mode == "vulkan_layer" and options.get("write_vk_layer", True):
                state["vulkan_writeback"] = vulkan_layer_win.write_vk_layer_path_env_file(
                    tx,
                    target.install_path,
                    plan.dest_dll.parent,
                    state["deployed"].get("vulkan_layer", "VK_LAYER_RESHADE"),
                )

        warnings = [i.message for i in report.issues if i.level.value == "warning"]
        warnings.extend(i.message for i in conflicts.issues if i.severity.value == "warning")
        msg = (
            f"已部署 ReShade（模式 {plan.mode}，API {plan.api.value}"
            + (f"，代理 {plan.proxy_dll_name}" if plan.proxy_dll_name else "，Vulkan 显式层")
            + "）。"
        )
        if warnings:
            msg += " 警告：" + "；".join(warnings)
        return InstallResult(success=True, message=msg, details=state)

    def _install_optiscaler(self, target: EnhancementTarget, options: dict[str, Any]) -> InstallResult:
        kit_path = options.get("optiscaler_kit") or get_optiscaler_kit_path()
        if not kit_path:
            raise BuusdoError("未配置 OptiScaler 工具包路径。")
        kit = Path(kit_path)
        conflicts = conflict.check_install_conflicts(
            target, mode="optiscaler", optiscaler_kit=kit
        )
        if conflicts.blocked:
            raise BuusdoError("; ".join(i.message for i in conflicts.issues if i.severity.value == "block"))
        report = preflight.check_install_preflight(target)
        if not report.ok:
            raise BuusdoError(
                "; ".join(i.message for i in report.issues if i.level.value == "error")
            )
        resolved = optiscaler.resolve_kit(kit)
        with Transaction() as tx:
            state = optiscaler.deploy(tx, target.install_path, resolved, target_name=target.name)
        return InstallResult(
            success=True,
            message="已调度神经画质增强组件（OptiScaler）；与路径追踪无关。",
            details={**state, "conflicts": [i.message for i in conflicts.issues]},
        )

    def _remix_toggle(self, target: EnhancementTarget, *, enable: bool) -> InstallResult:
        mode = "rtx_remix_enable" if enable else "rtx_remix_disable"
        conflicts = conflict.check_install_conflicts(target, mode=mode)
        if conflicts.blocked:
            raise BuusdoError("; ".join(i.message for i in conflicts.issues if i.severity.value == "block"))
        with Transaction() as tx:
            state = (
                rtx_remix.enable(tx, target.install_path, target_name=target.name)
                if enable
                else rtx_remix.disable(tx, target.install_path, target_name=target.name)
            )
        return InstallResult(success=True, message=state["copy"], details=state)

    def _apply_display_profile(
        self, target: EnhancementTarget, options: dict[str, Any]
    ) -> InstallResult:
        game_id = str(target.metadata.get("app_id") or target.name)
        profile = display_profile.DisplayProfile(
            name=str(options.get("profile_name") or target.name),
            hdr_preferred=bool(options.get("hdr_preferred", False)),
            resolution=options.get("resolution"),
            refresh_hz=options.get("refresh_hz"),
            color_space=options.get("color_space"),
            notes=str(options.get("notes") or "按游戏显示配置（诚实记录偏好，非强制改系统）"),
        )
        display_profile.set_game_profile(game_id, profile)
        applied = display_profile.apply_profile_noop(profile)
        update_game_config(game_id, display_profile=profile.name)
        return InstallResult(
            success=True,
            message="已保存该游戏的显示/HDR 偏好配置。",
            details=applied,
        )

    def _resolve_api(self, options: dict[str, Any], target: EnhancementTarget) -> GraphicsApi | None:
        raw = options.get("api")
        if raw is None:
            game_id = str(target.metadata.get("app_id") or target.name)
            raw = get_game_pref(game_id, "graphics_api") or target.metadata.get("graphics_api")
        if raw is None:
            return detect_graphics_api(target.executable) if target.executable else None
        try:
            return GraphicsApi(str(raw).lower())
        except ValueError as exc:
            raise BuusdoError(f"Unknown graphics API: {raw}") from exc

    def _resolve_target_prefs(
        self, target: EnhancementTarget, options: dict[str, Any]
    ) -> EnhancementTarget:
        game_id = str(target.metadata.get("app_id") or target.name)
        fields: dict[str, Any] = {}
        if options.get("executable"):
            fields["executable"] = str(options["executable"])
        if options.get("api"):
            fields["graphics_api"] = str(options["api"])
        if options.get("steam_id3"):
            fields["steam_id3"] = str(options["steam_id3"])
        cfg = update_game_config(game_id, **fields) if fields else load_game_config(game_id)
        return self._apply_saved_prefs(target, cfg)

    def _apply_saved_prefs(self, target: EnhancementTarget, cfg: dict[str, Any]) -> EnhancementTarget:
        prefs = cfg.get("prefs") or {}
        exe = target.executable
        exe_raw = prefs.get("executable") or cfg.get("executable")
        if exe_raw:
            candidate = Path(str(exe_raw))
            if candidate.is_file():
                exe = candidate
        meta = dict(target.metadata)
        api = prefs.get("graphics_api") or cfg.get("graphics_api")
        if api:
            meta["graphics_api"] = api
        if prefs.get("steam_id3") or cfg.get("steam_id3"):
            meta["steam_id3"] = prefs.get("steam_id3") or cfg.get("steam_id3")
        return EnhancementTarget(
            name=target.name,
            install_path=target.install_path,
            executable=exe,
            metadata=meta,
        )
