# Conflict export JSON schema

| Version | Notes |
|--------|--------|
| 1 | `mode`, `blocked`, `diffs`; optional `triple_matrix_summary` |
| 2 | Requires `schema_version: 2` and `triple_matrix_summary.issue_counts` (+ `issue_codes`) |

Migration: call `buusdo.core.conflict_preview.migrate_conflict_export(payload)` before reading
older exports. Live UI export always writes the current version (`CONFLICT_EXPORT_SCHEMA_VERSION`).

Fixture: `docs/fixtures/conflict_export_v2.json` (and `conflict_export_v1.json` for upgrade tests).
