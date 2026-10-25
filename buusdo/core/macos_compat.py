"""Discover Game Porting Toolkit / CrossOver / Bridgeplay config locations (C5).

Only filesystem discovery / config writes — no injection.
"""

from __future__ import annotations

import configparser
import json
import re
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


def discover_bridgeplay_config_files(config_dir: Path) -> dict[str, Path | None]:
    """Locate real Bridgeplay ini/plist candidates (prefer existing MetalFX-named files)."""
    root = Path(config_dir)
    ini: Path | None = None
    plist: Path | None = None
    preferred_ini = (
        "metalfx.ini",
        "MetalFX.ini",
        "bridgeplay.ini",
        "settings.ini",
        "config.ini",
    )
    preferred_plist = (
        "metalfx.plist",
        "MetalFX.plist",
        "com.bridgeplay.settings.plist",
        "settings.plist",
    )
    for name in preferred_ini:
        p = root / name
        if p.is_file():
            ini = p
            break
    if ini is None:
        for p in sorted(root.rglob("*.ini")):
            if p.is_file() and "metalfx" in p.name.lower():
                ini = p
                break
    for name in preferred_plist:
        p = root / name
        if p.is_file():
            plist = p
            break
    if plist is None:
        for p in sorted(root.rglob("*.plist")):
            if p.is_file() and "metalfx" in p.name.lower():
                plist = p
                break
    return {"ini": ini, "plist": plist}


def _upsert_ini_section_key(text: str, section: str, key: str, value: str) -> str:
    """Upsert key=value under [section] while preserving comments and line order."""
    lines = text.splitlines(keepends=True)
    if not lines and text:
        lines = [text]
    section_re = re.compile(rf"^\[{re.escape(section)}\]\s*$", re.IGNORECASE)
    any_section = re.compile(r"^\[.+\]\s*$")
    key_re = re.compile(rf"^(\s*{re.escape(key)}\s*=\s*).*$", re.IGNORECASE)
    start = None
    end = len(lines)
    for i, line in enumerate(lines):
        if section_re.match(line.strip()):
            start = i
            break
    if start is None:
        suffix = "" if (not text or text.endswith("\n")) else "\n"
        block = f"{suffix}[{section}]\n{key} = {value}\n"
        return text + block
    for j in range(start + 1, len(lines)):
        if any_section.match(lines[j].strip()):
            end = j
            break
    body = lines[start + 1 : end]
    replaced = False
    for k, line in enumerate(body):
        m = key_re.match(line.rstrip("\n\r"))
        if m:
            nl = "\n" if line.endswith("\n") else ""
            body[k] = f"{m.group(1)}{value}{nl}"
            replaced = True
            break
    if not replaced:
        insert = f"{key} = {value}\n"
        # Keep blank trailing line of section if present.
        if body and body[-1].strip() == "":
            body.insert(len(body) - 1, insert)
        else:
            body.append(insert)
    return "".join(lines[: start + 1] + body + lines[end:])


def _merge_ini_text(existing: str, *, enable: bool, quality: str, scale: float | None) -> str:
    text = existing
    # Prefer [MetalFX]; also upgrade legacy / GPTK [metalfx] keys in-place.
    has_metalfx = bool(re.search(r"(?im)^\[MetalFX\]\s*$", text))
    has_legacy = bool(re.search(r"(?im)^\[metalfx\]\s*$", text))
    section = "MetalFX" if has_metalfx or not has_legacy else "metalfx"
    text = _upsert_ini_section_key(text, section, "enabled", "true" if enable else "false")
    text = _upsert_ini_section_key(text, section, "quality", str(quality))
    text = _upsert_ini_section_key(text, section, "upscaler", "metalfx")
    if scale is not None:
        text = _upsert_ini_section_key(text, section, "scale", str(float(scale)))
    if section != "MetalFX" and not has_metalfx:
        text = _upsert_ini_section_key(text, "MetalFX", "enabled", "true" if enable else "false")
        text = _upsert_ini_section_key(text, "MetalFX", "quality", str(quality))
        text = _upsert_ini_section_key(text, "MetalFX", "upscaler", "metalfx")
        if scale is not None:
            text = _upsert_ini_section_key(text, "MetalFX", "scale", str(float(scale)))
    # GPTK [renderer]: only touch upscaler (and api when enabling); keep comments/order.
    upscaler_val = "metalfx" if enable else "none"
    if not enable:
        m = re.search(r"(?im)^\[renderer\]\s*$([\s\S]*?)(?=^\[|\Z)", text)
        if m:
            um = re.search(r"(?im)^\s*upscaler\s*=\s*(.+)$", m.group(1))
            if um:
                upscaler_val = um.group(1).strip() or "none"
    text = _upsert_ini_section_key(text, "renderer", "upscaler", upscaler_val)
    if enable:
        # Only set api if missing — do not clobber an existing value.
        rend = re.search(r"(?im)^\[renderer\]\s*$([\s\S]*?)(?=^\[|\Z)", text)
        if not rend or not re.search(r"(?im)^\s*api\s*=", rend.group(1)):
            text = _upsert_ini_section_key(text, "renderer", "api", "metal")
    return text


def _merge_plist_text(existing: str, *, enable: bool, quality: str, scale: float | None) -> str:
    """Naive XML plist merge: upsert known MetalFX keys; rewrite whole dict if unparsable."""
    keys = {
        "metalfx.enabled": f"<{ 'true' if enable else 'false' }/>",
        "metalfx.quality": f"<string>{quality}</string>",
        "renderer.upscaler": "<string>metalfx</string>",
    }
    if scale is not None:
        keys["metalfx.scale"] = f"<real>{float(scale)}</real>"
    text = existing
    if "<plist" not in text or "<dict>" not in text:
        return bridgeplay_metalfx_file_contents(enable=enable, quality=quality, scale=scale)["plist"]
    for key, value_xml in keys.items():
        pattern = re.compile(
            rf"(<key>{re.escape(key)}</key>\s*)(<true/>|<false/>|<string>[^<]*</string>|<real>[^<]*</real>)",
            re.IGNORECASE,
        )
        if pattern.search(text):
            text = pattern.sub(rf"\1{value_xml}", text, count=1)
        else:
            text = text.replace("</dict>", f"\t<key>{key}</key>\n\t{value_xml}\n</dict>", 1)
    return text


def merge_bridgeplay_metalfx(
    config_dir: Path,
    *,
    game_name: str,
    enable: bool = True,
    quality: str = "balanced",
    scale: float | None = None,
    tx: Any = None,
) -> dict[str, Any]:
    """Merge MetalFX keys into discovered Bridgeplay ini/plist; fall back to sidecar write."""
    found = discover_bridgeplay_config_files(config_dir)
    contents = bridgeplay_metalfx_file_contents(enable=enable, quality=quality, scale=scale)
    result: dict[str, Any] = {
        "merged": [],
        "created": [],
        "found": {k: str(v) if v else None for k, v in found.items()},
    }

    def _write(path: Path, text: str) -> None:
        if tx is not None:
            tx.ensure_dir(path.parent)
            tx.write_text(path, text)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")

    ini_path = found.get("ini")
    if ini_path and Path(ini_path).is_file():
        merged = _merge_ini_text(
            Path(ini_path).read_text(encoding="utf-8", errors="replace"),
            enable=enable,
            quality=quality,
            scale=scale,
        )
        _write(Path(ini_path), merged)
        result["merged"].append(str(ini_path))
    else:
        dest = Path(config_dir) / "buusdo" / game_name / "metalfx.ini"
        _write(dest, contents["ini"])
        result["created"].append(str(dest))

    plist_path = found.get("plist")
    if plist_path and Path(plist_path).is_file():
        merged_plist = _merge_plist_text(
            Path(plist_path).read_text(encoding="utf-8", errors="replace"),
            enable=enable,
            quality=quality,
            scale=scale,
        )
        _write(Path(plist_path), merged_plist)
        result["merged"].append(str(plist_path))
    else:
        dest = Path(config_dir) / "buusdo" / game_name / "metalfx.plist"
        _write(dest, contents["plist"])
        result["created"].append(str(dest))

    json_dest = Path(config_dir) / "buusdo" / game_name / "metalfx_bridgeplay.json"
    _write(json_dest, contents["json"])
    result["created"].append(str(json_dest))
    return result
