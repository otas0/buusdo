"""Minimal i18n with C4-honest copy keys. Capability titles use cap.* keys from backends."""

from __future__ import annotations

from typing import Any

_LOCALE = "zh"

_STRINGS: dict[str, dict[str, str]] = {
    "zh": {
        "app.subtitle": "图形增强调度器 · 配置协调器",
        "action.scan": "扫描 Steam 库",
        "action.force_scan": "强制全量刷新",
        "action.cancel_scan": "取消扫描",
        "action.deploy": "部署增强",
        "action.uninstall": "卸载",
        "action.confirm_uninstall": "确认卸载「{name}」的增强？",
        "action.open_kit_folder": "打开工具包目录",
        "action.proton_note": "写入 Proton 启动备注",
        "action.crash_opt_in": "崩溃上报（脱敏）",
        "block.title": "已阻断 — 检测到不安全目标",
        "block.body": "存在反作弊或无法确认安全时一律拒绝，不可继续。（本页无「继续」按钮。）",
        "badge.deployed": "[已部署]",
        "badge.none": "[未部署]",
        "cap.reshade": "ReShade 后处理调度",
        "cap.reshade.desc": "部署 ReShade（D3D / OpenGL 代理 DLL，或 Vulkan 显式层）。",
        "cap.optiscaler": "神经画质增强（OptiScaler 附加组件）",
        "cap.optiscaler.desc": "与 ReShade 底座解耦；调度本地神经超分组件。与路径追踪是不同能力。",
        "cap.remix": "RTX Remix mod 管理",
        "cap.remix.desc": "仅管理已有的 RTX Remix 路径追踪 mod，不重建场景。",
        "cap.vkbasalt": "Vulkan 后处理调度（vkBasalt / vkSumi）",
        "cap.vkbasalt.desc": "通过环境变量与 Steam launch options 调度已有 Vulkan 后处理层。",
        "cap.goverlay": "Goverlay 一键唤起",
        "cap.goverlay.desc": "检测桌面入口并启动 Goverlay（若已安装）。",
        "cap.metalfx": "MetalFX 兼容层配置",
        "cap.metalfx.desc": "在兼容层中配置 MetalFX。禁止使用第三方超分商标表述。",
        "cap.display": "按游戏显示/HDR 配置",
        "cap.display.desc": "保存并协调每游戏显示偏好（分辨率/刷新率/HDR 偏好）。",
        "cap.dwm_hdr": "DWM SDR→HDR 色彩兜底",
        "cap.dwm_hdr.desc": "可选模块；Phase 3 才实现。",
        "copy.no_rt_claim": "不得表述为「已开启光线追踪」",
        "copy.approx": "近似",
        "wizard.title": "欢迎使用 buusdo",
        "wizard.hint": "请选择本地 ReShade / OptiScaler 工具包目录（本应用不附带二进制）。",
        "wizard.kit_ok": "工具包看起来完整",
        "wizard.kit_bad": "缺少必要 DLL",
        "conflict.title": "部署前冲突预览",
        "conflict.col.severity": "级别",
        "conflict.col.action": "动作",
        "conflict.col.path": "路径",
        "conflict.col.detail": "详情",
        "proton.missing_prefix": "未找到 Proton compatdata 前缀；请先用 Proton 启动一次该游戏。",
        "proton.incomplete_prefix": "Proton 前缀不完整（缺少 drive_c）；请先用 Proton 启动一次该游戏。",
        "proton.ok": "Proton 前缀正常",
        "proton.open_steam": "在 Steam 中打开",
        "proton.note_written": "已写入 Steam 启动备注：请先用 Proton 启动一次。",
        "proton.note_text": "请先用 Proton 启动一次 — buusdo",
        "scan.progress": "正在扫描游戏库…",
        "msg.uninstall_win": "已卸载 ReShade / OptiScaler / Vulkan 层写回。",
        "msg.uninstall_linux": "已移除 Linux 增强部署。",
        "msg.uninstall_macos": "MetalFX 兼容层配置已移除。",
        "msg.uninstall_none": "没有可移除的内容。",
        "msg.reshade_deployed": "已部署 ReShade（模式 {mode}，API {api}{proxy}）。",
        "msg.optiscaler_deployed": "已调度神经画质增强组件（OptiScaler）；与路径追踪无关。",
        "msg.display_applied": "已保存并尝试应用显示/HDR 偏好（Win32/CCD）；游戏退出后将尝试回滚。",
        "msg.dwm_recorded": "DWM HDR 原型意图已记录",
        "msg.preview_ok": "冲突预览已生成",
        "msg.preview_blocked": "预览发现阻断冲突",
        "msg.metalfx_written": "MetalFX 兼容层配置已写入。{log}",
        "msg.goverlay_launched": "已启动 Goverlay：{path}",
        "msg.reshade_proton": "已在 Proton 游戏目录部署 ReShade（{mode}，API {api}）。",
        "msg.vkbasalt_written": "已写入 vkBasalt 调度配置（近似后处理），并尝试写回 Steam 启动项。",
        "lang.name": "中文",
    },
    "en": {
        "app.subtitle": "Graphics enhancement scheduler · config coordinator",
        "action.scan": "Scan Steam library",
        "action.force_scan": "Force full refresh",
        "action.cancel_scan": "Cancel scan",
        "action.deploy": "Deploy",
        "action.uninstall": "Uninstall",
        "action.confirm_uninstall": "Uninstall enhancements for “{name}”?",
        "action.open_kit_folder": "Open kit folder",
        "action.proton_note": "Write Proton launch note",
        "action.crash_opt_in": "Crash reports (redacted)",
        "block.title": "Blocked — unsafe target detected",
        "block.body": "Anti-cheat or unverified safety always refuses. No continue-anyway control.",
        "badge.deployed": "[Deployed]",
        "badge.none": "[Not deployed]",
        "cap.reshade": "ReShade post-process scheduling",
        "cap.reshade.desc": "Deploy ReShade (D3D/OpenGL proxy DLL or Vulkan explicit layer).",
        "cap.optiscaler": "Neural upscaling (OptiScaler addon)",
        "cap.optiscaler.desc": "Decoupled from ReShade; schedules local neural upscalers. Distinct from path tracing.",
        "cap.remix": "RTX Remix mod management",
        "cap.remix.desc": "Manage existing RTX Remix path-tracing mods only; no scene rebuild.",
        "cap.vkbasalt": "Vulkan post-process scheduling (vkBasalt / vkSumi)",
        "cap.vkbasalt.desc": "Schedule existing Vulkan post-process layers via env / Steam launch options.",
        "cap.goverlay": "Launch Goverlay",
        "cap.goverlay.desc": "Detect desktop entry and launch Goverlay when installed.",
        "cap.metalfx": "MetalFX compatibility-layer config",
        "cap.metalfx.desc": "Configure MetalFX in a compat layer. Never third-party upscaler trademarks.",
        "cap.display": "Per-game display / HDR profile",
        "cap.display.desc": "Save and coordinate per-game display preferences.",
        "cap.dwm_hdr": "DWM SDR→HDR color fallback",
        "cap.dwm_hdr.desc": "Optional module; Phase 3 only.",
        "copy.no_rt_claim": "Must not claim \"ray tracing enabled\"",
        "copy.approx": "approximate",
        "wizard.title": "Welcome to buusdo",
        "wizard.hint": "Choose local ReShade / OptiScaler kit folders (binaries are not bundled).",
        "wizard.kit_ok": "Kit looks complete",
        "wizard.kit_bad": "Required DLL missing",
        "conflict.title": "Pre-deploy conflict preview",
        "conflict.col.severity": "Severity",
        "conflict.col.action": "Action",
        "conflict.col.path": "Path",
        "conflict.col.detail": "Detail",
        "proton.missing_prefix": "Proton compatdata prefix missing; launch once under Proton first.",
        "proton.incomplete_prefix": "Proton prefix incomplete (no drive_c); launch once under Proton first.",
        "proton.ok": "Proton prefix healthy",
        "proton.open_steam": "Open in Steam",
        "proton.note_written": "Wrote Steam launch note: launch once under Proton first.",
        "proton.note_text": "Launch once under Proton first — buusdo",
        "scan.progress": "Scanning game library…",
        "msg.uninstall_win": "Uninstalled ReShade / OptiScaler / Vulkan layer writeback.",
        "msg.uninstall_linux": "Removed Linux enhancement deployment.",
        "msg.uninstall_macos": "MetalFX compat config removed.",
        "msg.uninstall_none": "Nothing to remove.",
        "msg.reshade_deployed": "Deployed ReShade (mode {mode}, API {api}{proxy}).",
        "msg.optiscaler_deployed": "Scheduled neural upscaling (OptiScaler); unrelated to path tracing.",
        "msg.display_applied": "Saved and applied display/HDR prefs (Win32/CCD); will try rollback on exit.",
        "msg.dwm_recorded": "DWM HDR prototype intent recorded",
        "msg.preview_ok": "Conflict preview ready",
        "msg.preview_blocked": "Preview found blocking conflicts",
        "msg.metalfx_written": "MetalFX compat config written.{log}",
        "msg.goverlay_launched": "Launched Goverlay: {path}",
        "msg.reshade_proton": "Deployed ReShade into Proton game dir ({mode}, API {api}).",
        "msg.vkbasalt_written": "Wrote vkBasalt schedule config (approximate) and Steam launch options.",
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
