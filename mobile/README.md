# buusdo mobile client

Phone and tablet UI for the **companion** protocol. Desktop buusdo remains the
source of truth for installs and config writes.

Full product scope: [docs/MOBILE.md](../docs/MOBILE.md).  
Release track: [docs/RELEASE_1.1.0.md](../docs/RELEASE_1.1.0.md).

## Client stack (1.1.0)

**Flutter** — one codebase for iOS + Android, phone + tablet breakpoints.

Native SwiftUI / Jetpack Compose clients are optional later; they must speak
`buusdo.companion` protocol v1 (`status`, `history_summary`, `request_scan`,
`capabilities`, `ping` only).

## Layout

```
mobile/
  README.md          ← this file
  PROTOCOL.md        ← client-facing op cheat sheet
  flutter/           ← buusdo_companion (status + scan; tablet two-pane)
```

## Honesty (do not regress)

- Never expose Install / Inject / Uninstall controls that call desktop mutators
  directly from the phone.
- Never claim the phone GPU/RAM accelerates PC frames.
- Surface the same hardware doctrine as desktop About
  ([docs/HARDWARE_NOTES.md](../docs/HARDWARE_NOTES.md)).

## Local protocol smoke (no Flutter required)

```bash
python -c "
from buusdo.companion import CompanionHost
h = CompanionHost(host_label='dev', paired=True)
print(h.handle({'protocol_version': 1, 'op': 'status'}).to_dict())
"
```

## Next implementation steps

1. `flutter create` under `mobile/flutter` with package name `buusdo_companion`.
2. Pairing screen → LAN URL + code from desktop.
3. Status + history list; scan request button (paired only).
4. Tablet: two-pane status | recent games.
