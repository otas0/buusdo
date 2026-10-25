"""Coexistence / mutual-exclusion checks for enhancement components."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from buusdo.core import optiscaler, reshade, rtx_remix
from buusdo.core.backend import EnhancementTarget


class ConflictSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    BLOCK = "block"


@dataclass
class ConflictIssue:
    severity: ConflictSeverity
    code: str
    message: str


@dataclass
class ConflictReport:
    issues: list[ConflictIssue] = field(default_factory=list)

    @property
    def blocked(self) -> bool:
        return any(i.severity is ConflictSeverity.BLOCK for i in self.issues)


# Filenames both OptiScaler kits and ReShade commonly touch.
_SHARED_NAMES = frozenset(
    {
        "dxgi.dll",
        "d3d9.dll",
        "d3d11.dll",
        "opengl32.dll",
        "nvngx.dll",
        "ReShade.ini",
        "OptiScaler.ini",
    }
)


def check_optiscaler_reshade(game_dir: Path, optiscaler_kit: Path | None = None) -> ConflictReport:
    report = ConflictReport()
    rs = reshade.status(game_dir)
    op = optiscaler.status(game_dir)

    if rs.get("installed") and op.get("installed"):
        report.issues.append(
            ConflictIssue(
                ConflictSeverity.WARNING,
                "both_installed",
                "ReShade 与 OptiScaler 均已部署；请确认代理 DLL 未互相覆盖",
            )
        )

    kit_files: set[str] = set()
    if optiscaler_kit and optiscaler_kit.is_dir():
        kit_files = {p.name.lower() for p in optiscaler_kit.iterdir() if p.is_file()}

    deployed = (rs.get("state") or {}).get("deployed") or {}
    reshade_names = set()
    for key in ("dll", "ini", "vulkan_json"):
        val = deployed.get(key)
        if val:
            reshade_names.add(Path(val).name.lower())

    overlap = (kit_files | reshade_names) & _SHARED_NAMES
    # Also check intended OptiScaler copy vs existing ReShade proxy
    if rs.get("installed") and kit_files:
        collision = kit_files & reshade_names
        if collision:
            report.issues.append(
                ConflictIssue(
                    ConflictSeverity.BLOCK,
                    "filename_collision",
                    f"OptiScaler 与 ReShade 文件名碰撞：{', '.join(sorted(collision))}",
                )
            )
        elif overlap:
            report.issues.append(
                ConflictIssue(
                    ConflictSeverity.WARNING,
                    "shared_proxy_names",
                    f"存在常见代理文件名重叠风险：{', '.join(sorted(overlap))}",
                )
            )
    return report


def check_remix_d3d9_proxy(game_dir: Path, *, deploying_reshade_proxy: str | None = None) -> ConflictReport:
    """Remix bridge often owns d3d9.dll — mutually exclusive with ReShade d3d9 proxy."""
    report = ConflictReport()
    remix = rtx_remix.status(game_dir)
    proxy = (deploying_reshade_proxy or "").lower()

    if remix.get("present") and remix.get("enabled") is not False:
        if proxy == "d3d9.dll" or (game_dir / "d3d9.dll").is_file() and remix.get("present"):
            if proxy == "d3d9.dll":
                report.issues.append(
                    ConflictIssue(
                        ConflictSeverity.BLOCK,
                        "remix_d3d9_mutex",
                        "RTX Remix mod 已占用/依赖 d3d9.dll；禁止同时部署 ReShade d3d9 代理。"
                        "请改用 dxgi/其他 API，或先禁用 Remix。",
                    )
                )
            elif remix.get("enabled") is True and proxy in {"dxgi.dll", "d3d11.dll"}:
                report.issues.append(
                    ConflictIssue(
                        ConflictSeverity.WARNING,
                        "remix_with_other_proxy",
                        "Remix 已启用且将部署其他代理 DLL；可能互扰，请仅在明确需要时继续。",
                    )
                )
    return report


def check_install_conflicts(
    target: EnhancementTarget,
    *,
    mode: str,
    optiscaler_kit: Path | None = None,
    reshade_proxy: str | None = None,
) -> ConflictReport:
    report = ConflictReport()
    if mode == "optiscaler":
        report.issues.extend(check_optiscaler_reshade(target.install_path, optiscaler_kit).issues)
    if mode == "reshade":
        report.issues.extend(
            check_remix_d3d9_proxy(target.install_path, deploying_reshade_proxy=reshade_proxy).issues
        )
        report.issues.extend(check_optiscaler_reshade(target.install_path, None).issues)
    if mode.startswith("rtx_remix"):
        rs = reshade.status(target.install_path)
        deployed = (rs.get("state") or {}).get("deployed") or {}
        if Path(str(deployed.get("dll", ""))).name.lower() == "d3d9.dll":
            report.issues.append(
                ConflictIssue(
                    ConflictSeverity.BLOCK,
                    "reshade_d3d9_blocks_remix",
                    "已部署 ReShade d3d9 代理；请先卸载后再启用 RTX Remix mod。",
                )
            )
    return report
