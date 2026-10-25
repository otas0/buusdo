"""Discover Game Porting Toolkit / CrossOver / Bridgeplay config locations (C5).

Only filesystem discovery — no injection.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CompatLayer:
    id: str
    title: str
    config_dir: Path
    log_candidates: tuple[Path, ...]


def discover_compat_layers(home: Path | None = None) -> list[CompatLayer]:
    home = home or Path.home()
    found: list[CompatLayer] = []

    # Game Porting Toolkit (common Homebrew / user layouts)
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

    # CrossOver bottles
    cx = home / "Library" / "Application Support" / "CrossOver" / "Bottles"
    if cx.is_dir():
        found.append(
            CompatLayer(
                id="crossover",
                title="CrossOver",
                config_dir=cx,
                log_candidates=(
                    home / "Library" / "Logs" / "CrossOver",
                    cx,
                ),
            )
        )

    # Bridgeplay (if present)
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


def metalfx_options_payload(*, enable: bool = True, quality: str = "balanced") -> dict:
    """Config payload for MetalFX via compat layer — never labeled DLSS (C4)."""
    return {
        "enhancement": "metalfx_compat",
        "metalfx_enabled": enable,
        "metalfx_quality": quality,
        "copy": "MetalFX 兼容层配置（禁止使用第三方超分商标表述）",
    }


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
