from __future__ import annotations

import json
import pathlib

import streamlit as st

_EVENTS_FILE = pathlib.Path(__file__).parent / "events.json"


def load_events() -> dict[str, str | None]:
    """Read events from events.json.

    Returns {event_name: final_url_or_None}.
    Falls back to an empty dict if the file is missing or malformed.
    """
    try:
        data = json.loads(_EVENTS_FILE.read_text())
        return {
            r["Event Name"]: r.get("Final URL") or None
            for r in data
            if r.get("Event Name")
        }
    except (json.JSONDecodeError, KeyError, TypeError):
        st.warning("Could not load events — check events.json for formatting errors.", icon="⚠️")
        return {}
    except FileNotFoundError:
        return {}
