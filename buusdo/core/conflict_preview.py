"""Build a file-level conflict / diff preview before deploy."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from buusdo.core import conflict, optiscaler, reshade, rtx_remix
from buusdo.core.backend import EnhancementTarget
from buusdo.core.graphics_detect import GraphicsApi
from buusdo.core.reshade import plan_deploy, resolve_kit

# Export JSON schema for conflict preview payloads (UI copy/export).
# v1: mode/blocked/diffs (+ optional triple_matrix_summary)
# v2: requires triple_matrix_summary.issue_counts + schema_version field
CONFLICT_EXPORT_SCHEMA_VERSION = 2


@dataclass(frozen=True)
class FileDiff:
    path: str
    action: str  # create | overwrite | restore | conflict
    detail: str = ""


def migrate_conflict_export(payload: dict[str, Any]) -> dict[str, Any]:
    """Upgrade a conflict-export dict in-place-ish to CONFLICT_EXPORT_SCHEMA_VERSION."""
    out = dict(payload)
    version = int(out.get("schema_version") or 1)
    if version < 2:
        summary = dict(out.get("triple_matrix_summary") or {})
        summary.setdefault(
            "issue_counts",
            {"block": 0, "warning": 0, "info": 0},
        )
        summary.setdefault("issue_codes", [])
        summary.setdefault("blocked", bool(out.get("blocked")))
        out["triple_matrix_summary"] = summary
        out["schema_version"] = 2
        version = 2
    out["schema_version"] = CONFLICT_EXPORT_SCHEMA_VERSION
    return out


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
    by_sev = {"block": 0, "warning": 0, "info": 0}
    for issue in report.issues:
        by_sev[issue.severity.value] = by_sev.get(issue.severity.value, 0) + 1
    summary = {
        "reshade_proxy": proxy,
        "optiscaler_kit": str(optiscaler_kit) if optiscaler_kit else None,
        "remix_present": bool(remix.get("present")),
        "remix_enabled": remix.get("enabled"),
        "issue_counts": by_sev,
        "blocked": report.blocked,
        "issue_codes": [i.code for i in report.issues],
    }
    return {
        "schema_version": CONFLICT_EXPORT_SCHEMA_VERSION,
        "mode": "triple_matrix",
        "blocked": report.blocked,
        "remix": remix,
        "triple_matrix_summary": summary,
        "diffs": [d.__dict__ for d in diffs],
    }
