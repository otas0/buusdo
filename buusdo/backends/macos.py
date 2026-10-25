"""macOS backend: compatibility-layer MetalFX config only (C5).

Forbidden: DYLD_INSERT_LIBRARIES, task_for_pid, mach_inject, or any dylib injection.
Allowed: read/write compat-layer config, set env vars, read compat-layer logs.
When target safety cannot be confirmed, default to block.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from buusdo.core import anticheat_guard
from buusdo.core.backend import (
    Capability,
    EnhancementBackend,
    EnhancementTarget,
    InstallResult,
)
from buusdo.core.errors import UnsafeTargetError
from buusdo.core.platform_detect import HostPlatform
from buusdo.core.transaction import Transaction

# Banned identifiers — present so tests / review can assert C5.
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

    def list_capabilities(self, target: EnhancementTarget) -> list[Capability]:
        return [
            Capability(
                id="metalfx_compat",
                title="MetalFX 兼容层配置",
                description=(
                    "在 Game Porting Toolkit / CrossOver / Bridgeplay 等兼容层中"
                    "配置 MetalFX（Metal 4 / Tahoe 26+）。"
                    "不得表述为 DLSS。"
                ),
                available=True,
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

        marker = compat_root / "buusdo_metalfx.json"
        with Transaction() as tx:
            tx.ensure_dir(compat_root)
            # Honest wording: MetalFX compat-layer config — never "DLSS" (C4).
            tx.write_text(
                marker,
                json.dumps(
                    {
                        "target": target.name,
                        "enhancement": "metalfx_compat",
                        "options": options,
                    },
                    indent=2,
                )
                + "\n",
            )
        return InstallResult(
            success=True,
            message="MetalFX 兼容层配置已写入（scaffold）。",
            details={"marker": str(marker)},
        )

    def uninstall(self, target: EnhancementTarget) -> InstallResult:
        anticheat_guard.check(target, HostPlatform.MACOS)
        options: dict[str, Any] = {}
        compat_root = self._compat_config_root(target, options)
        if compat_root is None:
            return InstallResult(success=True, message="Nothing to remove.")
        marker = compat_root / "buusdo_metalfx.json"
        with Transaction() as tx:
            if marker.exists():
                tx.delete(marker)
        return InstallResult(success=True, message="MetalFX 兼容层配置已移除。")

    def status(self, target: EnhancementTarget) -> dict[str, Any]:
        compat_root = self._compat_config_root(target, {})
        marker = (compat_root / "buusdo_metalfx.json") if compat_root else None
        return {
            "platform": self.platform_id(),
            "installed": bool(marker and marker.exists()),
            "marker": str(marker) if marker and marker.exists() else None,
            "forbidden_apis": sorted(_FORBIDDEN_INJECTION_APIS),
        }

    def _compat_config_root(
        self, target: EnhancementTarget, options: dict[str, Any]
    ) -> Path | None:
        """Resolve a writable compat-layer config directory.

        Without an explicit, confirmed path, return None so install blocks (C5 safety).
        """
        explicit = options.get("compat_config_dir") or target.metadata.get("compat_config_dir")
        if explicit:
            return Path(explicit)
        # Fallback: per-target dir under install_path only if caller marked it safe.
        if target.metadata.get("compat_confirmed"):
            return target.install_path / ".buusdo" / "metalfx"
        return None
