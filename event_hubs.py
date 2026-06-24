"""Event Hub config — one workshop checklist for selected high-traffic events only.

Add entries to ``event_hubs.json`` (not the Google Sheet) before a big event.
See ``docs/EVENT_HUB.md``.
"""

from __future__ import annotations

import json
from typing import Any

from repo_json import read_repo_json


def _first_str(row: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        raw = row.get(key)
        if raw is None:
            continue
        s = str(raw).strip()
        if s:
            return s
    return None


def load_event_hub_configs() -> list[dict[str, str]]:
    """Return hub configs from ``event_hubs.json`` (may be empty)."""
    try:
        data = json.loads(read_repo_json("event_hubs.json"))
    except FileNotFoundError:
        return []
    except (json.JSONDecodeError, TypeError):
        return []

    if not isinstance(data, list):
        return []

    out: list[dict[str, str]] = []
    for row in data:
        if not isinstance(row, dict):
            continue
        event_name = _first_str(row, ("event_name", "Event Name", "event", "Event"))
        workshop = _first_str(row, ("workshop", "Workshop", "workshop_name", "Workshop name"))
        if not event_name or not workshop:
            continue
        hub_title = _first_str(row, ("hub_title", "Hub title", "title")) or event_name
        nav_title = _first_str(row, ("nav_title", "Nav title", "sidebar_title")) or hub_title
        page_path = _first_str(row, ("page", "page_path", "Page"))
        intro = _first_str(row, ("intro", "Intro", "notes")) or ""
        out.append(
            {
                "event_name": event_name,
                "workshop": workshop,
                "hub_title": hub_title,
                "nav_title": nav_title,
                "page": page_path or "",
                "intro": intro,
            }
        )
    return out


def get_event_hub(event_name: str | None) -> dict[str, str] | None:
    """Return hub config when ``event_name`` is configured for Event Hub."""
    if not event_name or event_name == "None":
        return None
    name = str(event_name).strip()
    for cfg in load_event_hub_configs():
        if cfg["event_name"] == name:
            return cfg
    return None


# Default Streamlit page path per event (when ``page`` is omitted in event_hubs.json).
_DEFAULT_HUB_PAGES: dict[str, str] = {
    "Virtual Dev Day (EMEA)": "pages/5_Virtual_Dev_Day_EMEA.py",
    "Virtual Dev Day (NOAM)": "pages/6_Virtual_Dev_Day_NOAM.py",
}


def is_event_hub_event(event_name: str | None) -> bool:
    return get_event_hub(event_name) is not None


def hub_page_path(cfg: dict[str, str]) -> str | None:
    """Return the page script path for a hub config, or None if unknown."""
    explicit = (cfg.get("page") or "").strip()
    if explicit:
        return explicit
    return _DEFAULT_HUB_PAGES.get(cfg["event_name"])
