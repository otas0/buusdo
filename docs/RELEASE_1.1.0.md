# Release track: 1.1.0

**Status:** planned next public release after unsigned [v1.0.0](https://github.com/otas0/buusdo/releases/tag/v1.0.0).
Do not tag `v1.1.0` until the gate below is green and a human publishes.

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
- App Store / Play Store submission polish
- Cloud pairing / WAN relay

## Gate (human)

- [ ] `pytest` green on CI for companion + hardware honesty tests
- [ ] Desktop companion host: `status` works; install endpoints absent
- [ ] User Issue (`companion`): one real phone **or** tablet simulator
      pair+status (no agent VM theater)
- [ ] Bump `__version__` / `pyproject.toml` to `1.1.0` **only** in the cut-week
      release PR (not earlier)
- [ ] README / SHARE_BLURB point at 1.1.0 **only after** the tag is published
- [ ] Draft unpublished until a human decides to publish
- [ ] `phase3/dwm-hdr` not merged into the 1.1.0 tag
- [ ] Developer ID / Authenticode still deferred (not a blocker)

## Versioning

Keep package `__version__` / `pyproject.toml` at `1.0.0` until cut week; bump to
`1.1.0` in the release PR, then tag `v1.1.0`.
