# Mobile companion (phone / tablet)

**Status:** shipped with **v1.1.0** (desktop). Mobile client ships as **GitHub
source + Android APK** (unsigned). No App Store / Play Store.

buusdo on phone or tablet is a **companion** to the desktop app. It does not
install ReShade, inject into PC/console games, or turn phone silicon into a
remote GPU. Desktop backends keep owning all mutating work (C1–C5).

## Honest scope

| In scope | Out of scope |
|----------|--------------|
| Read-only status: desktop online, last scan, recent games, install history summary | Inject / install / uninstall from the phone |
| Pairing a trusted device on the local network | WAN / cloud relay that can mutate configs |
| Trigger desktop **scan** or open a queued desktop action the user already allowed | Bypass anti-cheat (C1) or “continue anyway” |
| Honest capability copy aligned with desktop C4 + [HARDWARE_NOTES.md](HARDWARE_NOTES.md) | Claiming phone RAM/GPU “boosts” PC frames |
| Phone + tablet layouts of the same companion UI | Feature parity with full desktop PySide6 UI |
| Optional push/local notification when a desktop job finishes | Background remote control without pairing |

## Architecture

```
┌─────────────────┐   paired LAN HTTP (Bearer token; no TLS yet) ┌──────────────────┐
│ Mobile client   │ ◄─────────────────────────────────────────► │ Desktop host     │
│ (phone/tablet)  │   JSON companion protocol v1                 │ buusdo.companion │
└─────────────────┘                                              │ → EnhancementBackend
                                                                 └──────────────────┘
```

**Cleartext LAN risk (1.1.0 honesty):** v1 uses plain HTTP on the local network
plus a Bearer device token. Anyone who can sniff that LAN segment can observe
pairing codes and tokens. Prefer **Loopback only** for local smoke; keep pairing
short; unpair unused devices. LAN **HTTPS** is deferred past 1.1.0.

- **Protocol** lives in `buusdo/companion/` (shared schema + honesty guards).
- **Desktop host** exposes only allowlisted ops (`status`, `history_summary`,
  `request_scan`). Mutating install paths stay on the desktop UI / backends.
- **Mobile UI** is a separate client track under `mobile/` (not PySide6). First
  client target: Flutter (one codebase for iOS + Android phone/tablet). Native
  Swift/Kotlin clients may follow; they must speak the same protocol.

## Constraints that still apply

- **C1** — companion cannot offer a continue-anyway path around anti-cheat.
- **C2** — any future write that the desktop performs on behalf of a companion
  request still goes through `Transaction`.
- **C3** — no `if platform == …` in `core/` or `ui/`; companion dispatch stays in
  `companion/` + existing backend factories.
- **C4** — mobile copy must not claim “ray tracing enabled,” DLSS on macOS, or
  hardware tricks from [HARDWARE_NOTES.md](HARDWARE_NOTES.md).
- **C5** — macOS desktop host remains config-only; companion cannot invent
  injection just because the client is a phone.

## Pairing (v1)

1. Desktop user opens **Companion** and clicks **Start pairing** (server is off
   until then). Dialog shows LAN URL + 6-digit code (TTL ~5 minutes).
2. Optional **Loopback only** bind (`127.0.0.1`) for safer local smoke; default
   is LAN (`0.0.0.0`). Preference is stored in `settings.json` as
   `companion_loopback_only` and applied on desktop startup. The dialog disables
   the toggle while the host is running (stop first to change bind). **Copy pair
   URL** copies the loopback or LAN base URL matching the current bind.
3. Mobile `POST /v1/pair` with the code; desktop stores a device token under
   `user_config_dir/companion_devices.json` via `Transaction` (C2).
4. Mobile calls `POST /v1/rpc` with `Authorization: Bearer <token>`.
5. Unpair / clear-all on desktop removes tokens; companion refuses unknown tokens.

Desktop chrome shows a **Companion** chip with a truncated bind address while
the host is running; the tooltip keeps the full `host:port` (and last error).
Pairing is rate-limited (8 attempts / client / 60s → HTTP 429 with
`retry_after`). The Companion dialog shows a countdown; logs record the client
address only — never the pairing code.

No accounts, no cloud identity in v1. See [mobile/PROTOCOL.md](../mobile/PROTOCOL.md).

## Release gating

**1.1.0 cut:** desktop packages + this companion foundation ship on GitHub.
Mobile client = **source only** under `mobile/flutter/` (no store APK/IPA).
Pair + status remains a **user-report** on Issue **#13** (label `companion`) —
not agent VM theater; reports welcome after ship.

Checklist for reporters:
- [ ] Desktop: Start pairing (LAN or loopback as appropriate)
- [ ] Flutter client: pair with code → `status` RPC succeeds
- [ ] Phone **or** tablet screenshot attached to the Issue
- [ ] Note OS / Flutter build / bind mode (LAN vs loopback)

Release notes state clearly: companion ≠ mobile injection host.
`SHARE_BLURB` / README release links update **after** `v1.1.0` is published.

Optional setting (Companion dialog checkbox, **default off**):
`companion_persist_last_label` stores only the last paired **label** in
`settings.json` — never tokens (tokens remain Transaction-backed under
`companion_devices.json`). Clear-all unpaired devices also clears the saved
label. Default-on only with explicit human OK.

## GitHub mobile packages

| Asset | Where | Notes |
|-------|--------|-------|
| Flutter source + `android/` + `ios/` | `mobile/flutter/` | Scaffold via `scripts/companion_flutter_scaffold.sh` |
| Android APK (unsigned) | Actions `companion-apk` artifact / Release asset `buusdo-companion.apk` | Sideload; cleartext LAN HTTP enabled |
| iOS IPA | **Not** attached | Needs Apple signing; `ios/` sources only |

## Non-goals for 1.1.x

- App Store / Play Store listing
- Cloud sync of game configs
- Controlling console GPUs from the phone
- Replacing the desktop app
- LAN **HTTPS** / TLS pinning (v1 ships HTTP + Bearer token on LAN)
- Unsigned iOS IPA on GitHub (Apple signing required)

## Holds (still off for 1.1.x)

- Merge `phase3/dwm-hdr` into a release tag
- Require Developer ID notarization or Windows Authenticode
- App Store / Play Store packaging
