# Agent notes for buusdo

## Documentation language

**English is the default** for README, `docs/**`, Cursor rules, commit messages,
PR text, and agent replies unless the user explicitly asks for Chinese (or another
language).

- Do not add Chinese to new markdown or rules “for convenience.”
- **Exception:** end-user install/open guides under `docs/user-guide/` may ship
  one file per UI locale (`buusdo/locales/`). Other `docs/**` stay English;
  `scripts/check_docs_language.py` skips only that folder.
- UI string catalogs may still ship `zh` + `en` via `buusdo/core/i18n.py` (product
  localization). That is separate from repo documentation language.
- Product honesty rules (C4) apply in every language the UI shows.

## Hard constraints

See `docs/PROJECT.md` and `.cursor/rules/buusdo-constraints.mdc` (C1–C5).

## Verification style

Prefer **user reports** over complex agent smoke (VM/ISO/Explorer theater).
Fix what is already known from CI/logs/code; see `.cursor/rules/user-report-first.mdc`.
