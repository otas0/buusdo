# Feedback triage (post v0.1.0 preview)

Channel: [GitHub Issues](https://github.com/otas0/buusdo/issues).  
Labels: `launch`, `scan` (plus defaults).  
Do **not** agent-poll Actions or re-fire `workflow_dispatch` while waiting on feedback.

## 0.1.1 policy

**Fixes only** — no large features. Prefer:

1. **`launch`** — cannot start / missing PySide6 / crash on start  
2. **`scan`** — Steam library scan hangs, empty, cancel broken  
3. Deploy/uninstall / anti-cheat false positives  
4. Docs / install clarity (kits self-provide)

## Installer track (parallel, not 0.1.1 scope)

Unsigned Inno installer may be built now (Windows / CI `installer` workflow).  
Ship installer on GitHub when smoke passes; tag **`v1.0.0` only then**. Until then keep calling builds **preview**.

Out of band forever for preview:

- Authenticode / SmartScreen reputation  
- Phase 3 DWM HDR (stay isolated on `phase3/dwm-hdr`)  
- Calling the preview an “official release” or tagging `v1.*` early

## Share copy

See [SHARE_BLURB.md](SHARE_BLURB.md).
