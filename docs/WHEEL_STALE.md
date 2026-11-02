# Stale dist wheels

`dist/buusdo-0.1.0-py3-none-any.whl` (and any copy under `dist/payload/`) built
**before** `buusdo/locales/*.json` + `logo_wordmark.png` package-data is **stale**.
Do not ship it.

Rebuild and verify:

```bash
uvx --from build pyproject-build --wheel -o dist/fresh
python scripts/check_pyinstaller_datas.py dist/fresh/buusdo-*.whl
```

No PyInstaller onedir was present at last check — when one exists, run the same
script on that directory.

Preview release may be published (unsigned) after Explorer wordmark OK.
Authenticode / `0.1.1` remain on hold until cert dry-run + real `launch`/`scan` Issues.
Do not retag as `v1.*`.
