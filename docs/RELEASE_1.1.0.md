# Release track: 1.1.0

**Status:** published — [v1.1.0](https://github.com/otas0/buusdo-Graphics-Enhancement-Tool/releases/tag/v1.1.0).
**Product track:** complete — see [PROJECT_COMPLETE.md](PROJECT_COMPLETE.md).
Desktop packages via `.github/workflows/release.yml`. Mobile = GitHub APK +
Flutter source (no store). SHARE_BLURB / README updated post-publish.

## Why 1.1.0

Carry honesty + companion foundation that landed after 1.0.0, without waiting on
Apple Developer ID / Authenticode (**cancelled** — will not ship; [CODE_SIGNING.md](CODE_SIGNING.md)).

## Intended contents

1. **Hardware honesty** — [HARDWARE_NOTES.md](HARDWARE_NOTES.md) + About /
   capabilities rows (`buusdo.core.hardware_notes`). Already on `main`.
2. **Unsigned vs notarized docs** — honest Gatekeeper / signing checklist
   ([CODE_SIGNING.md](CODE_SIGNING.md)). Already on `main`.
3. **Mobile companion** — [MOBILE.md](MOBILE.md), `buusdo/companion/` protocol +
   LAN transport + pairing UI, Flutter client under `mobile/flutter/`.
4. Desktop Companion dialog (user-started LAN URL + code); tokens via
   `Transaction` under `user_config_dir`.
5. About rows for companion non-goals + links to MOBILE.md / HARDWARE_NOTES.md.
6. Release notes that say clearly: phone/tablet = companion, not injection host.

## Explicitly out of scope (final)

- Developer ID notarization / staple — **cancelled**
- Windows Authenticode — **cancelled**
- Phase 3 DWM HDR (`phase3/dwm-hdr` stays isolated)
- App Store / Play Store / iOS IPA
- Cloud pairing / WAN relay
- LAN HTTPS (cleartext honesty stays in MOBILE.md)

## Gate

- [x] `pytest` green on CI for companion + hardware honesty tests (ongoing on `main`)
- [x] Desktop companion host: `status` works; install endpoints absent
- [x] User Issue [#13](https://github.com/otas0/buusdo-Graphics-Enhancement-Tool/issues/13): non-blocking; closed with project complete
- [x] Bump `__version__` / `pyproject.toml` to `1.1.0` in this cut
- [x] README / SHARE_BLURB → 1.1.0 **after** the tag is published
- [x] Human decided to publish (ship-now request)
- [x] `phase3/dwm-hdr` not merged into the 1.1.0 tag
- [x] Developer ID / Authenticode **cancelled** (not deferred)
- [x] Human: product track complete at v1.1.0 shelf (2026-11-06)

## Versioning

Bump to `1.1.0` here, then tag `v1.1.0` to run the unsigned multi-platform
release workflow.
