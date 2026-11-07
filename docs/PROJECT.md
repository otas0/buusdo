# buusdo Graphics Enhancement Tool — project brief

## 1. What this project is

**Product line:** buusdo. **This product:** **buusdo Graphics Enhancement Tool**
(graphics / display enhancement track). It is **not** **buusdo Cybersecurity
Service Tool** — same brand family, separate product; do not mix repos, releases,
or support.

This repo is a cross-platform (Windows / Linux / macOS) desktop tool for improving
graphics experience. Core jobs are **automatic visual enhancement scheduling**
and **ray-tracing capability management**, plus a few tightly related system
items (per-game display profiles, HDR coordination).

It is not a rendering engine and not a game-mod authoring tool. In essence it is:

  **an enhancement capability scheduler + config coordinator.**

It reuses each platform’s existing enhancement ecosystem. It does not implement
injection hosts itself, does not implement rendering, and does not implement
ray tracing. It is not a cybersecurity / SOC / vulnerability-scanning product.

## 2. Platform capability boundaries (must be respected)

Graphics pipeline openness differs by OS. Feature parity across three platforms
is not a goal.

### Windows (fullest surface)
- Injection host: ReShade (D3D9/10/11/12, OpenGL, Vulkan)
- Neural upscaling: DLSS-class paths via ReShade addons or OptiScaler
- True path tracing: manage existing RTX Remix mods only; never rebuild scenes
- Color fallback: DWM SDR→HDR shader patch (optional module; Phase 3)

### Linux (schedule existing open-source stack)
- Native Linux games: Vulkan post-process layers (vkBasalt / vkSumi)
- Entry points: Goverlay, or env vars + Steam launch options
- Windows games under Proton: reuse Windows ReShade deploy logic into the
  Proton prefix, not the host filesystem
- Do not implement Vulkan layers or hooks in-tree

### macOS (config coordination only — no injection)
- No dylib injection. SIP and hardened runtime are system constraints; asking
  users to disable SIP is an unacceptable security cost.
- Only enhancement path: MetalFX (Metal 4 / Tahoe 26+), and routing DLSS-class
  options to MetalFX through compat layers (Game Porting Toolkit / CrossOver /
  Bridgeplay)
- Backend duties: detect runtime, write compat-layer MetalFX options, read
  compat-layer logs for confirmation
- When target safety cannot be confirmed, default to block

## 3. Hard constraints (violations are bugs)

### C1. Anti-cheat gate is a hard block, not a warning
- Every backend `install()` / inject / config write must start with
  `core.anticheat_guard.check(target, platform)`
- On detection, raise `UnsafeTargetError`; UI shows a non-bypassable block page
- Never offer “I understand the risk, continue”
- Semantics: presence of anti-cheat ⇒ refuse

### C2. All writes are transactional
- Must go through `core.transaction.Transaction`
- Semantics: snapshot before change → record each change → reverse-order restore
  on failure
- Uninstall must byte-restore original files
- No half-installed leftover state

### C3. Platform differences stay inside `backends/`
- No `if platform == "windows"` (or similar) in `core/` or `ui/`
- Dispatch only in `core/platform_detect.py` and `backends/__init__.py`
- UI talks only to the `EnhancementBackend` abstraction

### C4. Honest copy — no capability inflation
- Never claim “ray tracing enabled”
- Path tracing (RTX Remix mods) and neural upscaling must stay distinct
- Post-process approximations must be marked as approximations
- On macOS never claim “DLSS”; only “MetalFX compat-layer config”
- Never market “RAM as GPU,” free FPS from idle hardware, or VRAM spill as an upgrade —
  see [HARDWARE_NOTES.md](HARDWARE_NOTES.md)

### C5. macOS backend forbids injection
- No code that uses `DYLD_INSERT_LIBRARIES`, `task_for_pid`, `mach_inject`, or
  similar mechanisms
- macOS backend may only: read/write compat-layer configs, set env vars, read
  compat-layer logs

## 4. Locked stack

- Language: Python 3.11+
- UI: PySide6 (Qt 6.11+), shared across platforms
- Process / module enum: psutil
- PE parsing: pefile
- Injection (Windows only): ctypes → Win32 APIs
- Tests: pytest
- Packaging: pyside6-deploy
- Config persistence: JSON per game under the user config directory
- Mobile companion: protocol in `buusdo/companion/`; Flutter client under
  `mobile/` (phone + tablet). Companion is **not** an injection host — see
  [MOBILE.md](MOBILE.md)

Do not introduce: Electron, Tauri, Rust build chains, kernel drivers, or
in-house Vulkan/D3D hooks. Flutter for the companion client is an intentional
exception to the desktop PySide6-only UI rule.

### UI visual language

Light instrument panel (cool gray, ink type, monospace labels, single orange
accent, hairline borders). Cues from stark product UIs (Nothing / teenage
engineering) without copying cream/terracotta or purple-glow defaults. Theme
lives in `buusdo/ui/theme.py`.

### Steam properties URI probe

After clearing the URI cache, **Try open first** probes candidate deep links;
**Try next** (also **Ctrl+N** while enabled) advances to the next candidate and
shows that URI in the button tooltip. Exhaustion disables the control and the
shortcut together.
