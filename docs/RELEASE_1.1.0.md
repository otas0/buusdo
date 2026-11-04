# Release track: 1.1.0

**Status:** published — [v1.1.0](https://github.com/otas0/buusdo/releases/tag/v1.1.0).
Desktop packages via `.github/workflows/release.yml`. Mobile = GitHub source under
`mobile/flutter/` (no store). SHARE_BLURB / README updated post-publish.

## Why 1.1.0

Carry honesty + companion foundation that landed after 1.0.0, without waiting on
Apple Developer ID / Authenticode (those remain optional follow-ons).

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

## Explicitly deferred (not blockers)

- Developer ID notarization / staple (needs Apple certs — see CODE_SIGNING.md)
- Windows Authenticode
- Phase 3 DWM HDR (`phase3/dwm-hdr` stays isolated)
- App Store / Play Store submission (mobile ships as GitHub source only)
- Cloud pairing / WAN relay
- LAN HTTPS (cleartext honesty stays in MOBILE.md)

## Gate

- [x] `pytest` green on CI for companion + hardware honesty tests (ongoing on `main`)
- [x] Desktop companion host: `status` works; install endpoints absent
- [ ] User Issue [#13](https://github.com/otas0/buusdo/issues/13): pair+status
      report still welcome post-ship (not blocking this cut)
- [x] Bump `__version__` / `pyproject.toml` to `1.1.0` in this cut
- [x] README / SHARE_BLURB → 1.1.0 **after** the tag is published
- [x] Human decided to publish (ship-now request)
- [x] `phase3/dwm-hdr` not merged into the 1.1.0 tag
- [x] Developer ID / Authenticode still deferred

## Versioning

Bump to `1.1.0` here, then tag `v1.1.0` to run the unsigned multi-platform
release workflow.
