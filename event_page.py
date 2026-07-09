"""Shared event checklist UI — trial, guides, auto-grader, and badge for any event."""

from __future__ import annotations

from typing import Any

import streamlit as st

from events import load_events, load_event_workshops
from event_hubs import get_event_hub
from workshops import load_workshop_rows

_DEFAULT_INTRO = (
    "Follow the steps below in order. Use the same email for trial signup and the auto-grader."
)


def _workshop_row(workshop_title: str) -> dict[str, str] | None:
    for row in load_workshop_rows():
        if row.get("workshop") == workshop_title:
            return row
    return None


def _hub_workshops(hub: dict[str, Any]) -> list[str]:
    workshops = hub.get("workshops")
    if isinstance(workshops, list) and workshops:
        return [str(w).strip() for w in workshops if str(w).strip()]
    single = str(hub.get("workshop") or "").strip()
    return [single] if single else []


def _trial_event_names(hub: dict[str, Any]) -> list[str]:
    trial_events = hub.get("trial_events")
    if isinstance(trial_events, list) and trial_events:
        return [str(e).strip() for e in trial_events if str(e).strip()]
    return [hub["event_name"]]


def resolve_event_config(event_name: str) -> dict[str, Any]:
    """Build display config for ``event_name``.

    ``event_hubs.json`` overrides workshop lists for large events; otherwise workshops
    come from the optional **Workshop** column on the Events sheet.
    """
    hub = get_event_hub(event_name)
    if hub:
        return {
            "event_name": hub["event_name"],
            "title": hub.get("nav_title") or hub["event_name"],
            "intro": hub.get("intro") or _DEFAULT_INTRO,
            "workshops": _hub_workshops(hub),
            "trial_events": _trial_event_names(hub),
        }
    sheet_workshops = load_event_workshops(event_name)
    return {
        "event_name": event_name,
        "title": event_name,
        "intro": _DEFAULT_INTRO,
        "workshops": sheet_workshops,
        "trial_events": [event_name],
    }


def render_event_checklist(event_name: str, *, sync_selected_event: bool = False) -> None:
    """Render the full event checklist for ``event_name``.

    Set ``sync_selected_event`` on dedicated hub pages so Badge status and deep links
    see the right event. Do not set it from Event Page (selectbox owns that key).
    """
    cfg = resolve_event_config(event_name)
    workshops = cfg["workshops"]

    if sync_selected_event:
        st.session_state["selected_event"] = cfg["event_name"]

    st.header(f"🎯 {cfg['title']}")

    if cfg.get("intro"):
        st.markdown(cfg["intro"])

    st.warning(
        "Create a trial account using **AI Data Cloud**, not **Cortex Code CLI** — "
        "even if using the CLI in the hands-on lab.",
        icon="⚠️",
    )

    events = load_events()
    trial_names = cfg["trial_events"]

    st.divider()

    st.subheader("Step 1 — Snowflake trial")
    trial_links = [(name, events.get(name)) for name in trial_names]
    found = [(name, url) for name, url in trial_links if url]

    if found:
        if len(found) == 1:
            name, url = found[0]
            st.markdown(f"Sign up for a Snowflake trial account for **{name}**.")
            st.link_button("Open Trial Signup", url, type="primary")
        else:
            st.markdown("Sign up for a Snowflake trial account for this event.")
            for i, (name, url) in enumerate(found):
                st.link_button(
                    f"Open Trial Signup — {name}",
                    url,
                    type="primary",
                    key=f"trial_{i}",
                )
    else:
        st.info("Trial signup link coming soon.", icon="🔜")

    st.divider()

    st.subheader("Step 2 — Complete your lab")
    if not workshops:
        st.markdown(
            "Open **Guides & Answer Keys** and select the workshop you are attending."
        )
        st.page_link("pages/2_Guides_and_Answer_Keys.py", label="Guides & Answer Keys", icon="📚")
    elif len(workshops) == 1:
        workshop_row = _workshop_row(workshops[0])
        st.markdown(f"Workshop: **{workshops[0]}**")
        if workshop_row and (workshop_row.get("guide_url") or "").strip():
            st.link_button(
                workshop_row.get("guide_label") or "View Guide",
                workshop_row["guide_url"],
            )
        else:
            st.info("Guide link coming soon.", icon="🔜")
            st.page_link("pages/2_Guides_and_Answer_Keys.py", label="Guides & Answer Keys", icon="📚")
    else:
        st.markdown("Choose the guide for the lab you are attending:")
        for i, workshop in enumerate(workshops):
            workshop_row = _workshop_row(workshop)
            st.markdown(f"**{workshop}**")
            if workshop_row and (workshop_row.get("guide_url") or "").strip():
                st.link_button(
                    workshop_row.get("guide_label") or "View Guide",
                    workshop_row["guide_url"],
                    key=f"guide_{i}",
                )
            else:
                st.info("Guide link coming soon.", icon="🔜")

    st.divider()

    st.subheader("Step 3 — Auto-grader & answer key")
    st.markdown(
        "Generate your auto-grader SQL script (same email you used to register), "
        "paste it into a Snowflake worksheet, and run it in full."
    )
    if not workshops:
        st.page_link("pages/3_Auto-Grader.py", label="Go to Auto-Grader", icon="⚙️")
    elif len(workshops) == 1:
        if st.button("Go to Auto-Grader", type="primary", icon="⚙️"):
            st.session_state["auto_grader_workshop_preset"] = workshops[0]
            st.switch_page("pages/3_Auto-Grader.py")
    else:
        st.markdown("Open the auto-grader for the lab you completed:")
        for i, workshop in enumerate(workshops):
            if st.button(
                f"Auto-Grader — {workshop}",
                type="primary",
                icon="⚙️",
                key=f"grader_{i}",
            ):
                st.session_state["auto_grader_workshop_preset"] = workshop
                st.switch_page("pages/3_Auto-Grader.py")

    st.divider()

    st.subheader("Badge")
    st.markdown(
        "Complete the lab and run the auto-grader script to qualify for your badge. "
        "Allow **7 business days** after the event; check **Badge status** for updates."
    )
    st.page_link("pages/4_Badge_Status.py", label="Badge status", icon="🏅")
