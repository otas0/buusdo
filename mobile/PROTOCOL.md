# Companion protocol v1 (client cheat sheet)

Canonical types: `buusdo.companion.protocol`.

## Envelope

```json
{
  "protocol_version": 1,
  "op": "status",
  "request_id": "optional-id",
  "params": {}
}
```

Response:

```json
{
  "protocol_version": 1,
  "ok": true,
  "request_id": "optional-id",
  "op": "status",
  "data": {},
  "error": ""
}
```

## Allowed ops

HTTP `/v1/rpc` always requires a paired Bearer token. Protocol-level
`request_scan` also checks `CompanionHost.paired`.

| op | purpose |
|----|---------|
| `ping` | liveness |
| `status` | read-only host snapshot |
| `history_summary` | short history text |
| `capabilities` | honest capability rows |
| `request_scan` | ask desktop to queue a library scan |

## Forbidden (server rejects)

`install`, `uninstall`, `inject`, `deploy_reshade`, `write_config`,
`bypass_anticheat`, `enable_ray_tracing`, `ram_as_gpu`, and any unknown op.

## Transport (1.1.0)

LAN HTTP only — **no cloud relay**. Desktop starts the host when the user clicks
**Start pairing** in the Companion dialog.

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/v1/health` | none | liveness |
| POST | `/v1/pair` | body `{ "code": "######", "label": "…" }` | exchange pairing code → device token |
| POST | `/v1/rpc` | `Authorization: Bearer <token>` | companion protocol envelope |

Default listen port: **8765**. Base URL shown in the desktop dialog
(`http://<lan-ip>:8765`). Tokens are stored under the desktop
`user_config_dir/companion_devices.json` via `Transaction` (C2).
