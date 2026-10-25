"""Generate vkBasalt config templates (schedules existing layer; does not ship it)."""

from __future__ import annotations

from pathlib import Path

PRESETS: dict[str, dict] = {
    "cas": {
        "effects": "cas",
        "casSharpness": 0.4,
        "label": "CAS sharpening (approximate)",
    },
    "smaa": {
        "effects": "smaa",
        "smaaEdgeDetection": "luma",
        "smaaThreshold": 0.05,
        "label": "SMAA anti-aliasing (approximate)",
    },
    "contrast": {
        "effects": "contrastAdaptiveSharpening:cas",
        "casSharpness": 0.35,
        "label": "Contrast-oriented CAS stack (approximate)",
    },
    "cas_smaa": {
        "effects": "smaa:cas",
        "casSharpness": 0.3,
        "smaaEdgeDetection": "luma",
        "smaaThreshold": 0.05,
        "label": "SMAA + CAS (approximate)",
    },
}


def render_preset(name: str, *, sharpness: float | None = None) -> str:
    preset = PRESETS.get(name) or PRESETS["cas"]
    lines = [
        f"# buusdo vkBasalt preset: {name}",
        f"# {preset.get('label', name)} — approximate post-process",
        "# Requires system-installed vkBasalt / vkSumi.",
        f"effects = {preset['effects']}",
        "enableOnLaunch = True",
    ]
    cas = sharpness if sharpness is not None else preset.get("casSharpness")
    if cas is not None:
        lines.append(f"casSharpness = {float(cas):.2f}")
    if "smaaEdgeDetection" in preset:
        lines.append(f"smaaEdgeDetection = {preset['smaaEdgeDetection']}")
    if "smaaThreshold" in preset:
        lines.append(f"smaaThreshold = {preset['smaaThreshold']}")
    return "\n".join(lines) + "\n"


def write_template(
    dest: Path,
    *,
    sharpness: float = 0.4,
    preset: str = "cas",
) -> Path:
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(render_preset(preset, sharpness=sharpness), encoding="utf-8")
    return dest


def steam_launch_for(config_path: Path) -> str:
    return f'ENABLE_VKBASALT=1 VKBASALT_CONFIG_FILE="{config_path}" %command%'


def list_presets() -> list[str]:
    return sorted(PRESETS.keys())
