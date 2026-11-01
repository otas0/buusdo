# buusdo $VERSION

GitHub Releases only — **unsigned** Windows installer.

> **SmartScreen:** Windows may show “Windows protected your PC” / unknown publisher.
> That is expected for unsigned GitHub builds. Choose **More info → Run anyway** if you trust the SHA256.

## Assets (formal)

- `buusdo-setup-$VERSION.exe` — Inno Setup (Windows 10/11 x64), **not** Authenticode-signed
- `SHA256SUMS`
- `INSTALL.txt`

Do **not** publish Linux/macOS installers on this release.

## Optional experimental

- `buusdo-$VERSION-py3-none-any.whl` — advanced users / Linux / macOS (experimental)

## Supported

- **Windows 10/11** (primary)

## Experimental (no official installer)

- Linux, macOS — source / wheel only; in-app capabilities marked experimental

## You must provide

- Your own **ReShade** / **OptiScaler** kit folders (**not** bundled)

## Not in this release

- Authenticode / SmartScreen reputation / Microsoft Store
- DWM HDR injection (Phase 3 — unavailable by design)
- Ray tracing “enabled” claims
- Bundled third-party enhancement binaries

## Verify

```bat
certutil -hashfile buusdo-setup-$VERSION.exe SHA256
```

Compare to `SHA256SUMS`.

## Feedback / 1.0.1

https://github.com/otas0/buusdo/issues — About → Feedback opens the same URL.
