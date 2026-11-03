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
3. **Mobile companion foundation** — [MOBILE.md](MOBILE.md),
   `buusdo/companion/` protocol + honesty guards, `mobile/` client scaffold.
4. Desktop host stub that serves allowlisted companion ops only (no remote
   install/inject API).
5. Release notes that say clearly: phone/tablet = companion, not injection host.

## Explicitly deferred (not blockers)

- Developer ID notarization / staple (needs Apple certs — see CODE_SIGNING.md)
- Windows Authenticode
- Phase 3 DWM HDR (`phase3/dwm-hdr` stays isolated)
- App Store / Play Store submission polish
- Cloud pairing / WAN relay

## Gate (human)

- [ ] `pytest` green on CI for companion + hardware honesty tests
- [ ] Desktop companion host: `status` works; install endpoints absent
- [ ] At least one phone **or** tablet simulator build speaks protocol v1
      (user-reported — no agent VM theater)
- [ ] README / SHARE_BLURB point at 1.1.0 only after tag exists
- [ ] Draft unpublished until a human decides to publish

## Versioning

Keep package `__version__` / `pyproject.toml` at `1.0.0` until cut week; bump to
`1.1.0` in the release PR, then tag `v1.1.0`.
