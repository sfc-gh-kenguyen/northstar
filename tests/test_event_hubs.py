from __future__ import annotations

import json

import pytest

import event_hubs


def test_load_event_hub_configs_parses_entries(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = json.dumps(
        [
            {
                "event_name": "Big Event 2026",
                "workshop": "My Workshop",
                "hub_title": "Welcome",
                "nav_title": "Welcome",
                "intro": "Hello room",
            }
        ]
    )

    def fake_read(path: str) -> str:
        assert path == "event_hubs.json"
        return payload

    monkeypatch.setattr(event_hubs, "read_repo_json", fake_read)
    rows = event_hubs.load_event_hub_configs()
    assert len(rows) == 1
    assert rows[0]["event_name"] == "Big Event 2026"
    assert rows[0]["workshop"] == "My Workshop"
    assert rows[0]["hub_title"] == "Welcome"
    assert rows[0]["nav_title"] == "Welcome"
    assert rows[0]["intro"] == "Hello room"


def test_hub_page_path_default() -> None:
    cfg = {"event_name": "Virtual Dev Day (EMEA)", "page": ""}
    assert event_hubs.hub_page_path(cfg) == "pages/5_Virtual_Dev_Day_EMEA.py"


def test_get_event_hub_match(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        event_hubs,
        "load_event_hub_configs",
        lambda: [{"event_name": "Summit Day", "workshop": "Lab A", "hub_title": "Summit Day", "intro": ""}],
    )
    assert event_hubs.is_event_hub_event("Summit Day") is True
    assert event_hubs.get_event_hub("Summit Day")["workshop"] == "Lab A"
    assert event_hubs.is_event_hub_event("Other") is False
