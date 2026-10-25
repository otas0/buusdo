"""Build a file-level conflict / diff preview before deploy."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from buusdo.core import conflict, optiscaler, reshade, rtx_remix
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
    report = conflict.triple_matrix(target.install_path, optiscaler_kit=kit)
    for issue in report.issues:
        diffs.append(FileDiff("", "conflict", f"[{issue.severity.value}] {issue.message}"))
    return {
        "mode": "optiscaler",
        "blocked": report.blocked,
        "reshade_installed": reshade.status(target.install_path).get("installed"),
        "optiscaler_installed": optiscaler.status(target.install_path).get("installed"),
        "remix": rtx_remix.status(target.install_path),
        "matrix": "reshade+optiscaler+remix",
        "diffs": [d.__dict__ for d in diffs],
    }


def preview_triple_matrix(
    target: EnhancementTarget,
    *,
    reshade_kit: Path | None = None,
    optiscaler_kit: Path | None = None,
    api: GraphicsApi | None = None,
) -> dict:
    proxy = None
    diffs: list[FileDiff] = []
    if reshade_kit:
        plan = plan_deploy(
            target.install_path,
            resolve_kit(reshade_kit),
            executable=target.executable,
            api=api,
        )
        proxy = plan.proxy_dll_name
        diffs.append(FileDiff(str(plan.dest_dll), "plan", f"reshade {plan.mode}"))
    if optiscaler_kit and Path(optiscaler_kit).is_dir():
        for src in Path(optiscaler_kit).iterdir():
            if src.is_file() and src.suffix.lower() == ".dll":
                diffs.append(FileDiff(str(target.install_path / src.name), "plan", "optiscaler"))
    remix = rtx_remix.status(target.install_path)
    if remix.get("present"):
        diffs.append(FileDiff(str(remix.get("d3d9") or ""), "present", "rtx remix bridge"))
    report = conflict.triple_matrix(
        target.install_path, optiscaler_kit=optiscaler_kit, reshade_proxy=proxy
    )
    for issue in report.issues:
        diffs.append(FileDiff("", "conflict", f"[{issue.severity.value}] {issue.message}"))
    return {
        "mode": "triple_matrix",
        "blocked": report.blocked,
        "remix": remix,
        "diffs": [d.__dict__ for d in diffs],
    }
