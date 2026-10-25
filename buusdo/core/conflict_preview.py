"""Build a file-level conflict / diff preview before deploy."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from buusdo.core import conflict, optiscaler, reshade
from buusdo.core.backend import EnhancementTarget
from buusdo.core.graphics_detect import GraphicsApi
from buusdo.core.reshade import plan_deploy, resolve_kit


@dataclass(frozen=True)
class FileDiff:
    path: str
    action: str  # create | overwrite | restore | conflict
    detail: str = ""


def preview_reshade_deploy(
    target: EnhancementTarget,
    kit_path: Path,
    *,
    api: GraphicsApi | None = None,
) -> dict:
    kit = resolve_kit(kit_path)
    plan = plan_deploy(target.install_path, kit, executable=target.executable, api=api)
    diffs: list[FileDiff] = []
    if plan.dest_dll.exists():
        diffs.append(
            FileDiff(str(plan.dest_dll), "overwrite", "existing proxy/layer DLL will be snapshotted")
        )
    else:
        diffs.append(FileDiff(str(plan.dest_dll), "create", plan.mode))
    if plan.dest_ini is not None:
        action = "overwrite" if plan.dest_ini.exists() else "create"
        diffs.append(FileDiff(str(plan.dest_ini), action, "ReShade.ini"))
    if plan.vulkan_json_name:
        jp = plan.dest_dll.parent / plan.vulkan_json_name
        diffs.append(
            FileDiff(str(jp), "overwrite" if jp.exists() else "create", "Vulkan explicit layer JSON")
        )

    report = conflict.check_install_conflicts(
        target, mode="reshade", reshade_proxy=plan.proxy_dll_name
    )
    for issue in report.issues:
        diffs.append(FileDiff("", "conflict", f"[{issue.severity.value}] {issue.message}"))

    return {
        "mode": "reshade",
        "api": plan.api.value,
        "proxy": plan.proxy_dll_name,
        "blocked": report.blocked,
        "diffs": [d.__dict__ for d in diffs],
    }


def preview_optiscaler_deploy(target: EnhancementTarget, kit_path: Path) -> dict:
    kit = Path(kit_path)
    diffs: list[FileDiff] = []
    for src in kit.iterdir() if kit.is_dir() else []:
        if not src.is_file():
            continue
        if src.suffix.lower() not in {".dll", ".ini", ".json", ".txt"}:
            continue
        dest = target.install_path / src.name
        diffs.append(
            FileDiff(
                str(dest),
                "overwrite" if dest.exists() else "create",
                f"from kit:{src.name}",
            )
        )
    report = conflict.check_optiscaler_reshade(target.install_path, kit)
    for issue in report.issues:
        diffs.append(FileDiff("", "conflict", f"[{issue.severity.value}] {issue.message}"))
    return {
        "mode": "optiscaler",
        "blocked": report.blocked,
        "reshade_installed": reshade.status(target.install_path).get("installed"),
        "optiscaler_installed": optiscaler.status(target.install_path).get("installed"),
        "diffs": [d.__dict__ for d in diffs],
    }
