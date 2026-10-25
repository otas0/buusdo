from pathlib import Path

from buusdo.core.discovery import discover_steam_games


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_discover_steam_games(tmp_path: Path) -> None:
    steam = tmp_path / "Steam"
    library = tmp_path / "SteamLibrary"
    game_dir = library / "steamapps" / "common" / "Sample Game"
    game_dir.mkdir(parents=True)
    (game_dir / "game.exe").write_bytes(b"MZ")

    _write(
        steam / "steamapps" / "libraryfolders.vdf",
        f'''
"libraryfolders"
{{
	"0"
	{{
		"path"		"{steam.as_posix()}"
	}}
	"1"
	{{
		"path"		"{library.as_posix()}"
	}}
}}
''',
    )
    _write(
        library / "steamapps" / "appmanifest_42.acf",
        """
"AppState"
{
	"appid"		"42"
	"name"		"Sample Game"
	"installdir"		"Sample Game"
}
""",
    )
    # Proton prefix present
    (library / "steamapps" / "compatdata" / "42" / "pfx").mkdir(parents=True)

    games = discover_steam_games([steam])
    assert len(games) == 1
    g = games[0]
    assert g.name == "Sample Game"
    assert g.app_id == "42"
    assert g.install_path == game_dir
    assert g.proton_prefix is not None
    target = g.to_target()
    assert target.metadata["runtime"] == "proton"
    assert target.executable is not None
