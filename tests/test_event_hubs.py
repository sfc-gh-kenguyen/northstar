from __future__ import annotations

import json

import pytest

import event_hubs
import event_page


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

    monkeypatch.setattr(event_hubs, "_event_hubs_json_text", lambda: payload)
    rows = event_hubs.load_event_hub_configs()
    assert len(rows) == 1
    assert rows[0]["event_name"] == "Big Event 2026"
    assert rows[0]["workshop"] == "My Workshop"
    assert rows[0]["workshops"] == ["My Workshop"]
    assert rows[0]["trial_events"] == ["Big Event 2026"]
    assert rows[0]["hub_title"] == "Welcome"
    assert rows[0]["nav_title"] == "Welcome"
    assert rows[0]["intro"] == "Hello room"


def test_load_event_hub_configs_parses_multi_workshop(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = json.dumps(
        [
            {
                "event_name": "APAC Virtual (7/15/2026)",
                "nav_title": "APAC Virtual — Day 1",
                "workshops": ["Lab A", "Lab B"],
                "trial_events": ["APAC Virtual (7/15/2026)", "APAC Virtual (7/16/2026)"],
            }
        ]
    )

    monkeypatch.setattr(event_hubs, "_event_hubs_json_text", lambda: payload)
    rows = event_hubs.load_event_hub_configs()
    assert rows[0]["workshops"] == ["Lab A", "Lab B"]
    assert rows[0]["trial_events"] == [
        "APAC Virtual (7/15/2026)",
        "APAC Virtual (7/16/2026)",
    ]


def test_hub_page_path_default() -> None:
    cfg = {"event_name": "Pune (7/25/2026)", "page": ""}
    assert event_hubs.hub_page_path(cfg) == "pages/5_Pune.py"

    cfg_explicit = {
        "event_name": "Pune (7/25/2026)",
        "page": "pages/5_Pune.py",
    }
    assert event_hubs.hub_page_path(cfg_explicit) == "pages/5_Pune.py"


def test_get_event_hub_match(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        event_hubs,
        "load_event_hub_configs",
        lambda: [
            {
                "event_name": "Summit Day",
                "workshop": "Lab A",
                "workshops": ["Lab A"],
                "trial_events": ["Summit Day"],
                "hub_title": "Summit Day",
                "intro": "",
            }
        ],
    )
    assert event_hubs.is_event_hub_event("Summit Day") is True
    assert event_hubs.get_event_hub("Summit Day")["workshop"] == "Lab A"
    assert event_hubs.is_event_hub_event("Other") is False


def test_resolve_event_config_uses_hub_overlay(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        event_page,
        "get_event_hub",
        lambda name: {
            "event_name": name,
            "nav_title": "Pune (7/25/2026)",
            "intro": "Hello Pune",
            "workshops": ["Lab A", "Lab B"],
            "trial_events": [name],
        }
        if name == "Pune (7/25/2026)"
        else None,
    )
    cfg = event_page.resolve_event_config("Pune (7/25/2026)")
    assert cfg["title"] == "Pune (7/25/2026)"
    assert cfg["workshops"] == ["Lab A", "Lab B"]
    assert cfg["intro"] == "Hello Pune"


def test_resolve_event_config_defaults_without_hub(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(event_page, "get_event_hub", lambda _name: None)
    monkeypatch.setattr(
        event_page,
        "load_event_workshops",
        lambda name: ["Lab From Sheet"] if name == "Seoul (6/23/2026)" else [],
    )
    cfg = event_page.resolve_event_config("Seoul (6/23/2026)")
    assert cfg["title"] == "Seoul (6/23/2026)"
    assert cfg["workshops"] == ["Lab From Sheet"]
    assert cfg["trial_events"] == ["Seoul (6/23/2026)"]
    assert cfg["intro"]
