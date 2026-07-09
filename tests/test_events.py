from __future__ import annotations

import json

import pytest

import events


def test_workshops_from_value_single() -> None:
    assert events._workshops_from_value("CoCo Foundations: Getting Started with CoCo") == [
        "CoCo Foundations: Getting Started with CoCo"
    ]


def test_workshops_from_value_semicolon_separated() -> None:
    raw = (
        "Data Ingestion, Transformation, and Delivery with Snowflake; "
        "Creating Declarative Data Pipelines with Dynamic Tables"
    )
    assert events._workshops_from_value(raw) == [
        "Data Ingestion, Transformation, and Delivery with Snowflake",
        "Creating Declarative Data Pipelines with Dynamic Tables",
    ]


def test_load_event_records_includes_workshop(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = json.dumps(
        [
            {
                "Event Name": "Raleigh (7/8/2026)",
                "Final URL": "https://example.com/trial",
                "Workshop": "CoCo Foundations: Getting Started with CoCo",
            }
        ]
    )
    monkeypatch.setattr(events, "read_repo_json", lambda _path: payload)
    rec = events.load_event_records()["Raleigh (7/8/2026)"]
    assert rec["workshops"] == ["CoCo Foundations: Getting Started with CoCo"]


def test_load_event_workshops_missing_event(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(events, "load_event_records", lambda: {})
    assert events.load_event_workshops("Unknown") == []
