"""History rows prefer message_key + runtime t(); OK/FAIL are localized."""

from __future__ import annotations

from buusdo.core import history
from buusdo.core.i18n import reload_catalogs, set_locale, t


def test_append_event_stores_message_key(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(history, "_history_path", lambda: tmp_path / "history.jsonl")
    history.append_event(
        "install:reshade",
        target="Demo",
        success=True,
        message="legacy snapshot",
        message_key="msg.reshade_deployed",
        message_params={"mode": "addon", "api": "dx11", "proxy": ""},
    )
    events = history.list_events()
    assert len(events) == 1
    assert events[0]["message_key"] == "msg.reshade_deployed"
    assert events[0]["message"] == "legacy snapshot"


def test_history_status_labels_localize() -> None:
    reload_catalogs()
    set_locale("ja")
    assert t("history.ok") == "成功"
    assert t("history.fail") == "失敗"
    set_locale("de")
    assert t("mode.preview") == "Konfliktvorschau"
