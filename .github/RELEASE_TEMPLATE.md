# buusdo $VERSION

**Full release** (not preview). **Unsigned** — SmartScreen / Gatekeeper warnings are expected.

## Assets

| Platform | Asset | Notes |
|----------|-------|-------|
| Windows | `buusdo-setup-$VERSION.exe` | Inno installer (unsigned) |
| macOS | `buusdo-macos-$VERSION.zip` | `Buusdo.app` (unsigned) |
| Linux | `buusdo-linux-$VERSION.tar.gz` + `install_linux.sh` | Onedir and/or wheel helper |
| All | `buusdo-$VERSION-py3-none-any.whl` | Universal pip install |

## Install

- **Windows:** run Setup (SmartScreen may warn).
- **macOS:** unzip → open `Buusdo.app` (Gatekeeper may warn; right-click → Open).
- **Linux:** `bash install_linux.sh` next to the wheel, or extract the onedir tarball.
- **Any OS (wheel):** `pip install buusdo-$VERSION-py3-none-any.whl "PySide6-Essentials==6.12.0"` then `python -m buusdo`.

## Honesty

- Capabilities differ by OS; **macOS is config-only** (no injection).
- Kits (**ReShade** / **OptiScaler**) are **BYO**, not bundled.
- No Authenticode / notarization in this build.
- No DWM HDR (Phase 3).
- Never claims “ray tracing enabled”.

## Verify

```bash
shasum -a 256 -c SHA256SUMS
```

Feedback: https://github.com/otas0/buusdo/issues
