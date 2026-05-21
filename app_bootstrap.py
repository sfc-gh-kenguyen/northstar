"""Shared setup for both Home.py and home_page.py entrypoints.

Streamlit Cloud may use either file as the main script; this module ensures
page config, event list, and session state are initialized exactly once per
session (set_page_config must not run twice).

Event selection lives on **Trial Sign Up**; optional ``?event=`` query (URL-encoded
name) preselects once per browser session.
"""

from __future__ import annotations

from urllib.parse import unquote_plus

import streamlit as st

from events import load_events
from instance_config import get_instance_label, instance_page_title_suffix


def init_app() -> None:
    # set_page_config must run at most once per session; this function runs every rerun.
    if "_northstar_page_config" not in st.session_state:
        title = "Snowflake Northstar" + instance_page_title_suffix()
        st.set_page_config(page_title=title, page_icon="❄️", layout="wide")
        st.session_state._northstar_page_config = True

    label = get_instance_label()
    if label and label != "1":
        st.sidebar.caption(f"Northstar instance **{label}**")

    events = load_events()

    if "selected_event" not in st.session_state:
        st.session_state.selected_event = "None"

    if "_northstar_event_query_applied" not in st.session_state:
        st.session_state._northstar_event_query_applied = True
        raw = st.query_params.get("event")
        if raw is not None:
            val = raw[0] if isinstance(raw, list) else raw
            val = str(val).strip()
            if val:
                name = unquote_plus(val)
                if name in events:
                    st.session_state.selected_event = name
