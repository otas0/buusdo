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

| op | paired? | purpose |
|----|---------|---------|
| `ping` | no | liveness |
| `status` | no | read-only host snapshot |
| `history_summary` | no | short history text |
| `capabilities` | no | honest capability rows |
| `request_scan` | **yes** | ask desktop to queue a library scan |

## Forbidden (server rejects)

`install`, `uninstall`, `inject`, `deploy_reshade`, `write_config`,
`bypass_anticheat`, `enable_ray_tracing`, `ram_as_gpu`, and any unknown op.

## Transport (1.1.0)

LAN only after desktop pairing. Exact HTTP paths / TLS pinning land with the
desktop host UI wiring — clients must not invent a cloud relay.
