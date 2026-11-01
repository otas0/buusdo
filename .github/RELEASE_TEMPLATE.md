# buusdo $VERSION

GitHub Releases channel only — **unsigned** Windows installer (SmartScreen may warn).

## Assets

- `buusdo-setup-$VERSION.exe` — Inno Setup installer (Windows 10/11 x64)
- `SHA256SUMS` — verify before running
- `INSTALL.txt` — three-step install
- Optional: `buusdo-$VERSION-py3-none-any.whl` (advanced / experimental hosts)

## Supported

- **Windows 10/11** (primary)

## Experimental (no official installer)

- Linux, macOS — use source / wheel; capabilities marked experimental in-app

## You must provide

- Your own **ReShade** / **OptiScaler** kit folders (not bundled)

## Not in this release

- Authenticode / SmartScreen reputation work
- Microsoft Store package
- DWM HDR injection (Phase 3)
- Ray tracing enablement claims
- Bundled third-party enhancement binaries

## Verify

```bat
certutil -hashfile buusdo-setup-$VERSION.exe SHA256
```

Compare to `SHA256SUMS`.

## Feedback

https://github.com/otas0/buusdo/issues
