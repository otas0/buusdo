"""Generate vkBasalt config templates (schedules existing layer; does not ship it)."""

from __future__ import annotations

from pathlib import Path

DEFAULT_TEMPLATE = """\
# buusdo-generated vkBasalt config (approximate post-process)
# Requires system-installed vkBasalt / vkSumi.
effects = cas
casSharpness = 0.4
enableOnLaunch = True
"""


def write_template(dest: Path, *, sharpness: float = 0.4) -> Path:
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    text = DEFAULT_TEMPLATE.replace("0.4", f"{sharpness:.2f}")
    dest.write_text(text, encoding="utf-8")
    return dest


def steam_launch_for(config_path: Path) -> str:
    return f'ENABLE_VKBASALT=1 VKBASALT_CONFIG_FILE="{config_path}" %command%'
