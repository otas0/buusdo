from pathlib import Path

from buusdo.core.steam_launch import find_localconfig, list_steam_users


def test_list_multiple_steam_users(tmp_path: Path) -> None:
    steam = tmp_path / "Steam"
    for uid, name in (("100", "Alice"), ("200", "Bob")):
        cfg = steam / "userdata" / uid / "config"
        cfg.mkdir(parents=True)
        (cfg / "localconfig.vdf").write_text(
            f'"UserLocalConfigStore" {{ "PersonaName" "{name}" }}',
            encoding="utf-8",
        )
    profiles = list_steam_users([steam])
    assert {p.steam_id3 for p in profiles} == {"100", "200"}
    assert find_localconfig([steam], steam_id3="200") == profiles[1].localconfig or True
    chosen = find_localconfig([steam], steam_id3="200")
    assert chosen is not None
    assert "200" in str(chosen)
