"""Per-game display / HDR profile coordination (cross-platform contract).

Platform-specific apply lives in backends; this module only stores profiles.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from buusdo.core.platform_detect import user_config_dir

SCHEMA_KEY = "display_profiles"


@dataclass
class DisplayProfile:
    name: str
    hdr_preferred: bool = False
    resolution: str | None = None  # e.g. "2560x1440"
    refresh_hz: int | None = None
    color_space: str | None = None  # srgb | hdr10 | dolby_vision (honest labels)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DisplayProfile:
        return cls(
            name=str(data.get("name") or "default"),
            hdr_preferred=bool(data.get("hdr_preferred", False)),
            resolution=data.get("resolution"),
            refresh_hz=data.get("refresh_hz"),
            color_space=data.get("color_space"),
            notes=str(data.get("notes") or ""),
        )


def _profiles_path() -> Path:
    return user_config_dir() / "display_profiles.json"


def load_profiles() -> dict[str, DisplayProfile]:
    path = _profiles_path()
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    profiles = raw.get("profiles") or {}
    return {k: DisplayProfile.from_dict(v) for k, v in profiles.items()}


def save_profiles(profiles: dict[str, DisplayProfile]) -> Path:
    path = _profiles_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "profiles": {k: v.to_dict() for k, v in profiles.items()},
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def get_game_profile(game_id: str) -> DisplayProfile | None:
    return load_profiles().get(game_id)


def set_game_profile(game_id: str, profile: DisplayProfile) -> None:
    profiles = load_profiles()
    profiles[game_id] = profile
    save_profiles(profiles)


def apply_profile_noop(profile: DisplayProfile) -> dict[str, Any]:
    """Default apply: record intent only. Backends may override with OS calls."""
    return {
        "applied": False,
        "mode": "record_only",
        "profile": profile.to_dict(),
        "note": "显示/HDR 配置已保存；具体 OS 切换由后端实现（Windows 完整，其他平台尽力）。",
    }
