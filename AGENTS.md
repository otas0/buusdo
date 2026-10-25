# Agent notes for buusdo

## Documentation language

**English is the default** for README, `docs/**`, Cursor rules, commit messages,
PR text, and agent replies unless the user explicitly asks for Chinese (or another
language).

- Do not add Chinese to new markdown or rules “for convenience.”
- UI string catalogs may still ship `zh` + `en` via `buusdo/core/i18n.py` (product
  localization). That is separate from repo documentation language.
- Product honesty rules (C4) apply in every language the UI shows.

## Hard constraints

See `docs/PROJECT.md` and `.cursor/rules/buusdo-constraints.mdc` (C1–C5).
