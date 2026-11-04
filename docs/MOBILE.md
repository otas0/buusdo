# Mobile companion (phone / tablet)

**Status:** foundation for the **1.1.0** track. Not a second injection host.

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

Ship into **1.1.0** only when:

1. Protocol + honesty + transport unit tests are green on CI.
2. Desktop host serves `status` / paired `request_scan` without install APIs.
3. **User-report gate:** at least one real phone **or** tablet simulator
   completes pair + status (file a GitHub Issue with label `companion` —
   **no agent VM / ISO theater**).
4. Release notes state clearly: companion ≠ mobile injection host.
5. Do **not** bump `__version__` / SHARE_BLURB until the cut-week release PR /
   published `v1.1.0` tag.

## Non-goals for 1.1.0

- App Store / Play Store listing polish
- Cloud sync of game configs
- Controlling console GPUs from the phone
- Replacing the desktop app
- LAN **HTTPS** / TLS pinning (post-1.1.0 hardening; v1 ships HTTP + Bearer token on LAN)

## Holds (do not do in companion PRs)

- Bump `__version__` / `pyproject.toml` / SHARE_BLURB before the cut-week
  release PR / published `v1.1.0`
- Merge `phase3/dwm-hdr` into the 1.1.0 tag
- Require Developer ID notarization or Windows Authenticode for 1.1.0
