from pathlib import Path

from buusdo.core.steam_launch import set_launch_options
from buusdo.core.transaction import Transaction


def test_set_launch_options_insert(tmp_path: Path) -> None:
    local = tmp_path / "localconfig.vdf"
    local.write_text(
        '''
"UserLocalConfigStore"
{
	"Software"
	{
		"Valve"
		{
			"Steam"
			{
				"apps"
				{
					"570"
					{
						"LastPlayed"		"1"
					}
				}
			}
		}
	}
}
''',
        encoding="utf-8",
    )
    with Transaction() as tx:
        result = set_launch_options(tx, local, "570", "ENABLE_VKBASALT=1 %command%")
    text = local.read_text(encoding="utf-8")
    assert "LaunchOptions" in text
    assert "ENABLE_VKBASALT=1" in text
    assert result["app_id"] == "570"
