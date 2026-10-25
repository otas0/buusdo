from pathlib import Path

from buusdo.core.crash_report import capture_exception, redact
from buusdo.core.i18n import set_locale, t
from buusdo.core.vkbasalt_template import steam_launch_for, write_template


def test_i18n_switches_and_keeps_c4_keys() -> None:
    set_locale("zh")
    assert "光线追踪" in t("copy.no_rt_claim") or "不得" in t("copy.no_rt_claim")
    set_locale("en")
    assert "ray tracing" in t("copy.no_rt_claim").lower()
    assert "metalfx" in t("cap.metalfx").lower()
    assert "dlss" not in t("cap.metalfx").lower()


def test_redact_paths(monkeypatch) -> None:
    monkeypatch.setenv("BUUSDO_CRASH_REPORTS", "1")
    text = redact(str(Path.home() / "secret" / "file.txt"))
    assert str(Path.home()) not in text
    path = capture_exception(RuntimeError(f"boom at {Path.home()}/x"), context={"p": str(Path.home())})
    assert path is not None
    body = path.read_text(encoding="utf-8")
    assert str(Path.home()) not in body


def test_vkbasalt_template(tmp_path: Path) -> None:
    conf = write_template(tmp_path / "vkBasalt.conf", sharpness=0.5)
    assert "cas" in conf.read_text(encoding="utf-8")
    assert "0.50" in conf.read_text(encoding="utf-8")
    assert "ENABLE_VKBASALT" in steam_launch_for(conf)
