from buusdo.core.vdf import parse_vdf


def test_parse_libraryfolders() -> None:
    text = """
"libraryfolders"
{
	"0"
	{
		"path"		"/home/user/.steam/steam"
		"apps"
		{
			"570"		"1"
		}
	}
	"1"
	{
		"path"		"/mnt/games/SteamLibrary"
	}
}
"""
    data = parse_vdf(text)
    folders = data["libraryfolders"]
    assert folders["0"]["path"] == "/home/user/.steam/steam"
    assert folders["1"]["path"] == "/mnt/games/SteamLibrary"


def test_parse_appmanifest() -> None:
    text = """
"AppState"
{
	"appid"		"570"
	"name"		"Dota 2"
	"installdir"		"dota 2 beta"
}
"""
    data = parse_vdf(text)
    assert data["AppState"]["name"] == "Dota 2"
    assert data["AppState"]["installdir"] == "dota 2 beta"
