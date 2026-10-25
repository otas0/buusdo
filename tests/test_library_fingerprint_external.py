from pathlib import Path

from buusdo.core.library_cache import _fingerprint, invalidate_cache, load_cached_games


def test_fingerprint_includes_external_library(tmp_path: Path, monkeypatch) -> None:
    steam = tmp_path / "Steam"
    external = tmp_path / "ExtLib"
    (steam / "steamapps").mkdir(parents=True)
    (external / "steamapps").mkdir(parents=True)
    (external / "steamapps" / "appmanifest_9.acf").write_text(
        '"AppState"{"appid""9""name""Z""installdir""Z"}', encoding="utf-8"
    )
    (external / "steamapps" / "common" / "Z").mkdir(parents=True)
    (steam / "steamapps" / "libraryfolders.vdf").write_text(
        f'"libraryfolders"{{"0"{{"path""{external.as_posix()}"}}}}',
        encoding="utf-8",
    )
    monkeypatch.setattr("buusdo.core.library_cache.user_config_dir", lambda: tmp_path / "cfg")
    fp = _fingerprint([steam])
    assert any("appmanifest_9.acf" in k for k in fp)
    invalidate_cache()
    games = load_cached_games([steam])
    # discovery needs installdir present
    assert isinstance(games, list)
