"""Windows backend: ReShade / OptiScaler scheduling, RTX Remix mod management."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from buusdo.core import anticheat_guard, history, optiscaler, preflight, reshade, rtx_remix
from buusdo.core.backend import (
    Capability,
    EnhancementBackend,
    EnhancementTarget,
    InstallResult,
)
from buusdo.core.config_store import (
    get_optiscaler_kit_path,
    get_reshade_kit_path,
    load_game_config,
    update_game_config,
)
from buusdo.core.discovery import discover_steam_games, list_executable_candidates
from buusdo.core.errors import BuusdoError
from buusdo.core.graphics_detect import GraphicsApi, detect_graphics_api
from buusdo.core.platform_detect import HostPlatform, steam_roots
from buusdo.core.transaction import Transaction


class WindowsBackend(EnhancementBackend):
    def platform_id(self) -> str:
        return HostPlatform.WINDOWS.value

    def discover_games(self) -> list[EnhancementTarget]:
        games = discover_steam_games(steam_roots(HostPlatform.WINDOWS))
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
        mode = str(options.get("mode") or "reshade")
        target = self._resolve_target_prefs(target, options)

        try:
            if mode == "reshade":
                result = self._install_reshade(target, options)
            elif mode == "optiscaler":
                result = self._install_optiscaler(target, options)
            elif mode == "rtx_remix_enable":
                result = self._remix_enable(target)
            elif mode == "rtx_remix_disable":
                result = self._remix_disable(target)
            else:
                raise BuusdoError(f"Unknown Windows install mode: {mode}")
        except Exception as exc:
            history.append_event(
                f"install:{mode}",
                target=target.name,
                success=False,
                message=str(exc),
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
        result = InstallResult(
            success=True,
            message="已卸载 ReShade / OptiScaler（事务恢复覆盖文件）。",
            details=details,
        )
        history.append_event(
            "uninstall",
            target=target.name,
            success=True,
            message=result.message,
            details=details,
        )
        return result

    def status(self, target: EnhancementTarget) -> dict[str, Any]:
        return {
            "platform": self.platform_id(),
            "reshade": reshade.status(target.install_path),
            "optiscaler": optiscaler.status(target.install_path),
            "rtx_remix": rtx_remix.status(target.install_path),
            "installed": reshade.status(target.install_path).get("installed")
            or optiscaler.status(target.install_path).get("installed"),
            "executables": target.metadata.get("executables")
            or [str(p) for p in list_executable_candidates(target.install_path)],
            "game_config": load_game_config(str(target.metadata.get("app_id") or target.name)),
        }

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
        with Transaction() as tx:
            state = reshade.deploy(tx, plan, target_name=target.name)
        warnings = [i.message for i in report.issues if i.level.value == "warning"]
        msg = (
            f"已部署 ReShade（模式 {plan.mode}，API {plan.api.value}"
            + (f"，代理 {plan.proxy_dll_name}" if plan.proxy_dll_name else "，Vulkan 显式层")
            + "）。"
        )
        if warnings:
            msg += " 警告：" + "；".join(warnings)
        if plan.mode == "vulkan_layer":
            msg += " 请按 state 中的 steam_launch_hint 配置启动项。"
        return InstallResult(
            success=True,
            message=msg,
            details={
                **state,
                "preflight": [
                    {"level": i.level.value, "code": i.code, "message": i.message}
                    for i in report.issues
                ],
            },
        )

    def _install_optiscaler(self, target: EnhancementTarget, options: dict[str, Any]) -> InstallResult:
        kit_path = options.get("optiscaler_kit") or get_optiscaler_kit_path()
        if not kit_path:
            raise BuusdoError("未配置 OptiScaler 工具包路径。")
        report = preflight.check_install_preflight(target)
        if not report.ok:
            raise BuusdoError("; ".join(i.message for i in report.issues if i.level.value == "error"))
        kit = optiscaler.resolve_kit(Path(kit_path))
        with Transaction() as tx:
            state = optiscaler.deploy(tx, target.install_path, kit, target_name=target.name)
        return InstallResult(
            success=True,
            message="已调度神经画质增强组件（OptiScaler）；与路径追踪无关。",
            details=state,
        )

    def _remix_enable(self, target: EnhancementTarget) -> InstallResult:
        with Transaction() as tx:
            state = rtx_remix.enable(tx, target.install_path, target_name=target.name)
        return InstallResult(success=True, message=state["copy"], details=state)

    def _remix_disable(self, target: EnhancementTarget) -> InstallResult:
        with Transaction() as tx:
            state = rtx_remix.disable(tx, target.install_path, target_name=target.name)
        return InstallResult(success=True, message=state["copy"], details=state)

    def _resolve_api(self, options: dict[str, Any], target: EnhancementTarget) -> GraphicsApi | None:
        raw = options.get("api")
        if raw is None:
            cfg = load_game_config(str(target.metadata.get("app_id") or target.name))
            raw = cfg.get("graphics_api")
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
        exe = options.get("executable")
        api = options.get("api")
        fields: dict[str, Any] = {}
        if exe:
            fields["executable"] = str(exe)
        if api:
            fields["graphics_api"] = str(api)
        if fields:
            cfg = update_game_config(game_id, **fields)
        else:
            cfg = load_game_config(game_id)
        return self._apply_saved_prefs(target, cfg)

    def _apply_saved_prefs(self, target: EnhancementTarget, cfg: dict[str, Any]) -> EnhancementTarget:
        exe = target.executable
        if cfg.get("executable"):
            candidate = Path(cfg["executable"])
            if candidate.is_file():
                exe = candidate
        meta = dict(target.metadata)
        if cfg.get("graphics_api"):
            meta["graphics_api"] = cfg["graphics_api"]
        return EnhancementTarget(
            name=target.name,
            install_path=target.install_path,
            executable=exe,
            metadata=meta,
        )
