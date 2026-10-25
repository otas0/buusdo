"""macOS backend: compatibility-layer MetalFX config only (C5)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from buusdo.core import anticheat_guard, history
from buusdo.core.backend import (
    Capability,
    EnhancementBackend,
    EnhancementTarget,
    InstallResult,
)
from buusdo.core.errors import UnsafeTargetError
from buusdo.core.library_cache import load_cached_games
from buusdo.core.macos_compat import (
    discover_compat_layers,
    find_recent_log,
    metalfx_options_payload,
)
from buusdo.core.platform_detect import HostPlatform, steam_roots
from buusdo.core.transaction import Transaction

_FORBIDDEN_INJECTION_APIS = frozenset(
    {
        "DYLD_INSERT_LIBRARIES",
        "task_for_pid",
        "mach_inject",
    }
)


class MacOSBackend(EnhancementBackend):
    def platform_id(self) -> str:
        return HostPlatform.MACOS.value

    def discover_games(self) -> list[EnhancementTarget]:
        games = load_cached_games(steam_roots(HostPlatform.MACOS))
        return [g.to_target() for g in games]

    def list_capabilities(self, target: EnhancementTarget) -> list[Capability]:
        layers = discover_compat_layers()
        return [
            Capability(
                id="metalfx_compat",
                title="MetalFX 兼容层配置",
                description=(
                    "在 Game Porting Toolkit / CrossOver / Bridgeplay 等兼容层中"
                    "配置 MetalFX。不得表述为 DLSS。"
                ),
                available=bool(layers) or bool(target.metadata.get("compat_confirmed")),
                notes=f"已发现兼容层：{', '.join(l.title for l in layers) or '无'}",
            ),
            Capability(
                id="compat_log_verify",
                title="兼容层日志确认",
                description="读取兼容层日志以确认 MetalFX 配置是否生效。",
                available=True,
            ),
        ]

    def install(self, target: EnhancementTarget, options: dict[str, Any] | None = None) -> InstallResult:
        anticheat_guard.check(target, HostPlatform.MACOS)
        options = options or {}

        compat_root = self._compat_config_root(target, options)
        if compat_root is None:
            raise UnsafeTargetError(
                target_name=target.name,
                reason="cannot confirm safe compatibility-layer target; blocked by default",
                evidence=["macos:compat_root_unconfirmed"],
            )

        payload = metalfx_options_payload(
            enable=bool(options.get("metalfx_enabled", True)),
            quality=str(options.get("metalfx_quality", "balanced")),
        )
        payload["target"] = target.name
        payload["options"] = {k: v for k, v in options.items() if k != "compat_config_dir"}

        marker = compat_root / "buusdo_metalfx.json"
        try:
            with Transaction() as tx:
                tx.ensure_dir(compat_root)
                tx.write_text(marker, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
        except Exception as exc:
            history.append_event("install:metalfx", target=target.name, success=False, message=str(exc))
            raise

        log_note = ""
        layers = discover_compat_layers()
        for layer in layers:
            log = find_recent_log(layer)
            if log:
                log_note = f" 最近日志：{log}"
                break

        result = InstallResult(
            success=True,
            message=f"MetalFX 兼容层配置已写入。{log_note}".strip(),
            details={"marker": str(marker), "payload": payload},
        )
        history.append_event(
            "install:metalfx",
            target=target.name,
            success=True,
            message=result.message,
            details=result.details,
        )
        return result

    def uninstall(self, target: EnhancementTarget) -> InstallResult:
        anticheat_guard.check(target, HostPlatform.MACOS)
        compat_root = self._compat_config_root(target, {})
        if compat_root is None:
            # Try discovered layer dirs for this target marker
            for layer in discover_compat_layers():
                marker = layer.config_dir / "buusdo" / target.name / "buusdo_metalfx.json"
                if marker.is_file():
                    with Transaction() as tx:
                        tx.delete(marker)
                    return InstallResult(success=True, message="MetalFX 兼容层配置已移除。")
            return InstallResult(success=True, message="Nothing to remove.")
        marker = compat_root / "buusdo_metalfx.json"
        with Transaction() as tx:
            if marker.exists():
                tx.delete(marker)
        return InstallResult(success=True, message="MetalFX 兼容层配置已移除。")

    def status(self, target: EnhancementTarget) -> dict[str, Any]:
        layers = discover_compat_layers()
        compat_root = self._compat_config_root(target, {})
        marker = (compat_root / "buusdo_metalfx.json") if compat_root else None
        return {
            "platform": self.platform_id(),
            "installed": bool(marker and marker.exists()),
            "marker": str(marker) if marker and marker.exists() else None,
            "compat_layers": [
                {"id": l.id, "title": l.title, "config_dir": str(l.config_dir)} for l in layers
            ],
            "forbidden_apis": sorted(_FORBIDDEN_INJECTION_APIS),
        }

    def _compat_config_root(
        self, target: EnhancementTarget, options: dict[str, Any]
    ) -> Path | None:
        explicit = options.get("compat_config_dir") or target.metadata.get("compat_config_dir")
        if explicit:
            return Path(explicit)

        layer_id = options.get("compat_layer") or target.metadata.get("compat_layer")
        layers = discover_compat_layers()
        if layer_id:
            for layer in layers:
                if layer.id == layer_id:
                    return layer.config_dir / "buusdo" / target.name
        if len(layers) == 1:
            return layers[0].config_dir / "buusdo" / target.name
        if target.metadata.get("compat_confirmed"):
            return target.install_path / ".buusdo" / "metalfx"
        return None
