"""Discover Game Porting Toolkit / CrossOver / Bridgeplay config locations (C5).

Only filesystem discovery / config writes — no injection.
"""

from __future__ import annotations

import configparser
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CompatLayer:
    id: str
    title: str
    config_dir: Path
    log_candidates: tuple[Path, ...]


BRIDGEPLAY_METALFX_KEYS = {
    "metalfx.enabled": "boolean",
    "metalfx.quality": "quality|balanced|performance",
    "metalfx.scale": "float",
    "renderer.upscaler": "metalfx",
}


def discover_compat_layers(home: Path | None = None) -> list[CompatLayer]:
    home = home or Path.home()
    found: list[CompatLayer] = []

    for path in (
        home / "Library" / "Application Support" / "Game Porting Toolkit",
        Path("/opt/homebrew/share/game-porting-toolkit"),
        Path("/usr/local/share/game-porting-toolkit"),
    ):
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


def bridgeplay_metalfx_file_contents(
    *,
    enable: bool = True,
    quality: str = "balanced",
    scale: float | None = None,
) -> dict[str, str]:
    """Return Bridgeplay MetalFX sidecar contents (json/ini/plist) for transactional write."""
    payload = metalfx_options_payload(
        enable=enable, quality=quality, layer_id="bridgeplay", scale=scale
    )
    cp = configparser.ConfigParser()
    cp["MetalFX"] = {
        "enabled": "true" if enable else "false",
        "quality": str(quality),
        "upscaler": "metalfx",
    }
    if scale is not None:
        cp["MetalFX"]["scale"] = str(float(scale))
    from io import StringIO

    buf = StringIO()
    cp.write(buf)
    scale_xml = (
        f"\n\t<key>metalfx.scale</key>\n\t<real>{float(scale)}</real>" if scale is not None else ""
    )
    plist = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        "<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" "
        "\"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">\n"
        "<plist version=\"1.0\">\n<dict>\n"
        f"\t<key>metalfx.enabled</key>\n\t<{'true' if enable else 'false'}/>\n"
        f"\t<key>metalfx.quality</key>\n\t<string>{quality}</string>\n"
        f"\t<key>renderer.upscaler</key>\n\t<string>metalfx</string>"
        f"{scale_xml}\n"
        "</dict>\n</plist>\n"
    )
    return {
        "json": json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        "ini": buf.getvalue(),
        "plist": plist,
    }


def write_bridgeplay_metalfx_files(
    config_dir: Path,
    *,
    game_name: str,
    enable: bool = True,
    quality: str = "balanced",
    scale: float | None = None,
) -> dict[str, str]:
    """Write Bridgeplay MetalFX settings as JSON + INI + plist under buusdo/<game>/."""
    dest_dir = config_dir / "buusdo" / game_name
    dest_dir.mkdir(parents=True, exist_ok=True)
    contents = bridgeplay_metalfx_file_contents(enable=enable, quality=quality, scale=scale)
    paths = {
        "json": dest_dir / "metalfx_bridgeplay.json",
        "ini": dest_dir / "metalfx.ini",
        "plist": dest_dir / "metalfx.plist",
    }
    for kind, path in paths.items():
        path.write_text(contents[kind], encoding="utf-8")
    return {k: str(v) for k, v in paths.items()}
