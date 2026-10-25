"""Discover Game Porting Toolkit / CrossOver / Bridgeplay config locations (C5).

Only filesystem discovery — no injection.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CompatLayer:
    id: str
    title: str
    config_dir: Path
    log_candidates: tuple[Path, ...]


# Bridgeplay-specific MetalFX keys (honest MetalFX wording only — C4/C5).
BRIDGEPLAY_METALFX_KEYS = {
    "metalfx.enabled": "boolean",
    "metalfx.quality": "quality|balanced|performance|quality",
    "metalfx.scale": "float",
    "renderer.upscaler": "metalfx",  # must not be set to third-party trademarks
}


def discover_compat_layers(home: Path | None = None) -> list[CompatLayer]:
    home = home or Path.home()
    found: list[CompatLayer] = []

    gptk_candidates = [
        home / "Library" / "Application Support" / "Game Porting Toolkit",
        Path("/opt/homebrew/share/game-porting-toolkit"),
        Path("/usr/local/share/game-porting-toolkit"),
    ]
    for path in gptk_candidates:
        if path.is_dir():
            found.append(
                CompatLayer(
                    id="gptk",
                    title="Game Porting Toolkit",
                    config_dir=path,
                    log_candidates=(path / "Logs", path / "logs"),
                )
            )
            break

    cx = home / "Library" / "Application Support" / "CrossOver" / "Bottles"
    if cx.is_dir():
        found.append(
            CompatLayer(
                id="crossover",
                title="CrossOver",
                config_dir=cx,
                log_candidates=(home / "Library" / "Logs" / "CrossOver", cx),
            )
        )

    bp = home / "Library" / "Application Support" / "Bridgeplay"
    if bp.is_dir():
        found.append(
            CompatLayer(
                id="bridgeplay",
                title="Bridgeplay",
                config_dir=bp,
                log_candidates=(bp / "Logs",),
            )
        )

    return found


def metalfx_options_payload(
    *,
    enable: bool = True,
    quality: str = "balanced",
    layer_id: str | None = None,
    scale: float | None = None,
) -> dict[str, Any]:
    """Config payload for MetalFX via compat layer — never labeled as third-party upscalers."""
    payload: dict[str, Any] = {
        "enhancement": "metalfx_compat",
        "metalfx_enabled": enable,
        "metalfx_quality": quality,
        "copy": "MetalFX 兼容层配置（禁止使用第三方超分商标表述）",
    }
    if layer_id == "bridgeplay":
        keys = {
            "metalfx.enabled": enable,
            "metalfx.quality": quality,
            "renderer.upscaler": "metalfx",
        }
        if scale is not None:
            keys["metalfx.scale"] = float(scale)
        payload["bridgeplay_keys"] = keys
        payload["key_schema"] = BRIDGEPLAY_METALFX_KEYS
    return payload


def find_recent_log(layer: CompatLayer) -> Path | None:
    candidates: list[Path] = []
    for root in layer.log_candidates:
        if root.is_file():
            candidates.append(root)
        elif root.is_dir():
            candidates.extend(p for p in root.rglob("*.log") if p.is_file())
    if not candidates:
        return None
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def write_bridgeplay_metalfx_config(
    config_dir: Path,
    *,
    game_name: str,
    enable: bool = True,
    quality: str = "balanced",
    scale: float | None = None,
) -> Path:
    """Write Bridgeplay MetalFX keys into a JSON sidecar (no injection)."""
    import json

    dest_dir = config_dir / "buusdo" / game_name
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = dest_dir / "metalfx_bridgeplay.json"
    payload = metalfx_options_payload(
        enable=enable, quality=quality, layer_id="bridgeplay", scale=scale
    )
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path
