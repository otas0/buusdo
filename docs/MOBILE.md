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
┌─────────────────┐   paired LAN (HTTPS or localhost tunnel)   ┌──────────────────┐
│ Mobile client   │ ◄──────────────────────────────────────► │ Desktop host     │
│ (phone/tablet)  │   JSON companion protocol v1               │ buusdo.companion │
└─────────────────┘                                            │ → EnhancementBackend
                                                               └──────────────────┘
```

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

## Pairing (v1 sketch)

1. Desktop shows a short pairing code + LAN URL (user-initiated).
2. Mobile enters the code; both store a device token (local only).
3. Unpair from desktop clears the token; companion refuses unsigned devices.

No accounts, no cloud identity in v1.

## Release gating

Ship into **1.1.0** only when:

1. Protocol + honesty unit tests are green.
2. Desktop host can serve `status` without opening install APIs.
3. At least one mobile client builds (debug) against the protocol on a phone **or**
   tablet simulator — user-reported, not agent VM theater.
4. Release notes state clearly: companion ≠ mobile injection host.

## Non-goals for 1.1.0

- App Store / Play Store listing polish
- Cloud sync of game configs
- Controlling console GPUs from the phone
- Replacing the desktop app
