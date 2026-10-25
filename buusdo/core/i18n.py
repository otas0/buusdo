"""Minimal i18n with C4-honest copy keys."""

from __future__ import annotations

from typing import Any

_LOCALE = "zh"

# Keys intentionally avoid overclaiming (C4).
_STRINGS: dict[str, dict[str, str]] = {
    "zh": {
        "app.subtitle": "图形增强调度器 · 配置协调器",
        "action.scan": "扫描 Steam 库",
        "action.force_scan": "强制全量刷新",
        "action.deploy": "部署增强",
        "action.uninstall": "卸载",
        "block.title": "已阻断 — 检测到不安全目标",
        "block.body": "存在反作弊或无法确认安全时一律拒绝，不可继续。（本页无「继续」按钮。）",
        "badge.deployed": "[已部署]",
        "badge.none": "[未部署]",
        "cap.reshade": "ReShade 后处理调度",
        "cap.optiscaler": "神经画质增强（OptiScaler 附加组件）",
        "cap.remix": "RTX Remix mod 管理（仅管理已有 mod，不重建场景）",
        "cap.metalfx": "MetalFX 兼容层配置（禁止第三方超分商标表述）",
        "copy.no_rt_claim": "不得表述为「已开启光线追踪」",
        "copy.approx": "近似",
        "wizard.title": "欢迎使用 buusdo",
        "wizard.hint": "请选择本地 ReShade / OptiScaler 工具包目录（本应用不附带二进制）。",
        "conflict.title": "部署前冲突预览",
        "proton.missing_prefix": "未找到 Proton compatdata 前缀；该游戏可能尚未以 Proton 启动过。",
        "scan.progress": "正在扫描游戏库…",
        "lang.name": "中文",
    },
    "en": {
        "app.subtitle": "Graphics enhancement scheduler · config coordinator",
        "action.scan": "Scan Steam library",
        "action.force_scan": "Force full refresh",
        "action.deploy": "Deploy",
        "action.uninstall": "Uninstall",
        "block.title": "Blocked — unsafe target detected",
        "block.body": "Anti-cheat or unverified safety always refuses. No continue-anyway control.",
        "badge.deployed": "[Deployed]",
        "badge.none": "[Not deployed]",
        "cap.reshade": "ReShade post-process scheduling",
        "cap.optiscaler": "Neural upscaling (OptiScaler addon scheduling)",
        "cap.remix": "RTX Remix mod management (existing mods only; no scene rebuild)",
        "cap.metalfx": "MetalFX compatibility-layer config (never third-party upscaler trademarks)",
        "copy.no_rt_claim": "Must not claim \"ray tracing enabled\"",
        "copy.approx": "approximate",
        "wizard.title": "Welcome to buusdo",
        "wizard.hint": "Choose local ReShade / OptiScaler kit folders (binaries are not bundled).",
        "conflict.title": "Pre-deploy conflict preview",
        "proton.missing_prefix": "Proton compatdata prefix missing; launch once under Proton first.",
        "scan.progress": "Scanning game library…",
        "lang.name": "English",
    },
}


def set_locale(locale: str) -> None:
    global _LOCALE
    if locale not in _STRINGS:
        raise ValueError(f"Unsupported locale: {locale}")
    _LOCALE = locale


def get_locale() -> str:
    return _LOCALE


def t(key: str, **kwargs: Any) -> str:
    table = _STRINGS.get(_LOCALE) or _STRINGS["zh"]
    text = table.get(key) or _STRINGS["zh"].get(key) or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    return text


def available_locales() -> list[str]:
    return sorted(_STRINGS.keys())
