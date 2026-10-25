"""Linux backend: vkBasalt scheduling + Proton ReShade (incl. Vulkan layer)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from buusdo.backends.goverlay import find_goverlay, launch_goverlay
from buusdo.core import anticheat_guard, conflict, history, preflight, reshade
from buusdo.core.proton_health import check_proton_prefix
from buusdo.core.i18n import t
from buusdo.core.vkbasalt_template import list_presets, steam_launch_for, write_template
from buusdo.core.backend import (
    Capability,
    EnhancementBackend,
    EnhancementTarget,
    InstallResult,
)
from buusdo.core.config_store import (
    get_game_pref,
    get_reshade_kit_path,
    load_game_config,
    update_game_config,
)
from buusdo.core.discovery import list_executable_candidates
from buusdo.core.errors import BuusdoError
from buusdo.core.graphics_detect import GraphicsApi, detect_graphics_api
from buusdo.core.library_cache import load_cached_games
from buusdo.core.platform_detect import HostPlatform, steam_roots
from buusdo.core.steam_launch import find_localconfig, set_launch_options
from buusdo.core.transaction import Transaction

_VKBASALT_STATE = ".buusdo/vkbasalt_env.json"


class LinuxBackend(EnhancementBackend):
    def platform_id(self) -> str:
        return HostPlatform.LINUX.value

    def discover_games(self, *, should_cancel=None) -> list[EnhancementTarget]:
        games = load_cached_games(
            steam_roots(HostPlatform.LINUX), should_cancel=should_cancel
        )
        out: list[EnhancementTarget] = []
        for g in games:
            if should_cancel and should_cancel():
                from buusdo.core.discovery import DiscoveryCancelled

                raise DiscoveryCancelled("scan cancelled")
            t = g.to_target()
            cfg = load_game_config(g.app_id)
            prefs = cfg.get("prefs") or {}
            exe_raw = prefs.get("executable") or cfg.get("executable")
            api = prefs.get("graphics_api") or cfg.get("graphics_api")
            meta = dict(t.metadata)
            if api:
                meta["graphics_api"] = api
            if prefs.get("steam_id3") or cfg.get("steam_id3"):
                meta["steam_id3"] = prefs.get("steam_id3") or cfg.get("steam_id3")
            exe = t.executable
            if exe_raw and Path(str(exe_raw)).is_file():
                exe = Path(str(exe_raw))
            out.append(
                EnhancementTarget(
                    name=t.name, install_path=t.install_path, executable=exe, metadata=meta
                )
            )
        return out

    def list_capabilities(self, target: EnhancementTarget) -> list[Capability]:
        is_proton = bool(target.metadata.get("proton_prefix") or target.metadata.get("runtime") == "proton")
        goverlay = find_goverlay()
        return [
            Capability(
                id="vkbasalt",
                title=t("cap.vkbasalt"),
                description=t("cap.vkbasalt.desc"),
                available=not is_proton,
                notes=f"{t('copy.approx')}; presets={','.join(list_presets())}",
            ),
            Capability(
                id="goverlay",
                title=t("cap.goverlay"),
                description=t("cap.goverlay.desc"),
                available=goverlay is not None,
                notes=str(goverlay) if goverlay else "goverlay not found",
            ),
            Capability(
                id="proton_reshade",
                title=t("cap.reshade"),
                description=t("cap.reshade.desc"),
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
            elif mode == "goverlay":
                launched = launch_goverlay()
                if not launched.get("launched"):
                    raise BuusdoError("未找到 Goverlay，请先安装 goverlay。")
                result = InstallResult(
                    success=True,
                    message=t("msg.goverlay_launched", path=launched["path"]),
                    details=launched,
                )
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
        result = InstallResult(success=True, message=t("msg.uninstall_linux"), details=details)
        history.append_event("uninstall", target=target.name, success=True, message=result.message, details=details)
        return result

    def status(self, target: EnhancementTarget) -> dict[str, Any]:
        info = reshade.status(target.install_path)
        env_path = target.install_path / _VKBASALT_STATE
        health = check_proton_prefix(target)
        return {
            "platform": self.platform_id(),
            "reshade": info,
            "installed": info.get("installed") or env_path.is_file(),
            "proton_prefix": target.metadata.get("proton_prefix"),
            "proton_health": None
            if health is None
            else {
                "ok": health.ok,
                "code": health.code,
                "message": health.message,
                "steam_uri": health.steam_uri,
                "steam_url": health.steam_url,
            },
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
        conflicts = conflict.check_install_conflicts(
            target, mode="reshade", reshade_proxy=plan.proxy_dll_name
        )
        if conflicts.blocked:
            raise BuusdoError(
                "; ".join(i.message for i in conflicts.issues if i.severity.value == "block")
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
                steam_id3 = (
                    options.get("steam_id3")
                    or target.metadata.get("steam_id3")
                    or get_game_pref(str(target.metadata["app_id"]), "steam_id3")
                )
                localconfig = find_localconfig(
                    steam_roots(HostPlatform.LINUX), steam_id3=steam_id3
                )
                if hint and localconfig:
                    state["launch_options"] = set_launch_options(
                        tx, localconfig, str(target.metadata["app_id"]), hint
                    )
        return InstallResult(
            success=True,
            message=t("msg.reshade_proton", mode=plan.mode, api=plan.api.value),
            details=state,
        )

    def _install_vkbasalt(self, target: EnhancementTarget, options: dict[str, Any]) -> InstallResult:
        conf = options.get("VKBASALT_CONFIG_FILE", "")
        template_path = target.install_path / ".buusdo" / "vkBasalt.conf"
        sharpness = float(options.get("cas_sharpness", 0.4))
        preset = str(options.get("vkbasalt_preset") or "cas")
        generate = not conf
        if generate:
            conf = str(template_path)
        launch = steam_launch_for(Path(conf))
        path = target.install_path / _VKBASALT_STATE
        details: dict[str, Any] = {"template": conf, "preset": preset}
        with Transaction() as tx:
            if generate:
                write_template(template_path, sharpness=sharpness, preset=preset)
                text = template_path.read_text(encoding="utf-8")
                tx.write_text(template_path, text)
            tx.ensure_dir(path.parent)
            tx.write_text(
                path,
                json.dumps(
                    {
                        "target": target.name,
                        "steam_launch_options": launch,
                        "config_file": conf,
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
                steam_id3 = (
                    options.get("steam_id3")
                    or target.metadata.get("steam_id3")
                    or get_game_pref(str(app_id), "steam_id3")
                )
                localconfig = find_localconfig(
                    steam_roots(HostPlatform.LINUX), steam_id3=steam_id3
                )
                if localconfig is None:
                    raise BuusdoError(
                        "未找到 Steam localconfig.vdf；若有多用户请先选择 steam_id3。"
                    )
                details["launch_options"] = set_launch_options(
                    tx, localconfig, str(app_id), launch
                )
        details["path"] = str(path)
        details["steam_launch_options"] = launch
        return InstallResult(
            success=True,
            message=t("msg.vkbasalt_written"),
            details=details,
        )
