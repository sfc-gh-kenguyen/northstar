"""Shared Event Hub checklist UI (one page per configured large event)."""

from __future__ import annotations

import streamlit as st

from events import load_events
from event_hubs import get_event_hub
from workshops import load_workshop_rows


def _workshop_row(workshop_title: str) -> dict[str, str] | None:
    for row in load_workshop_rows():
        if row.get("workshop") == workshop_title:
            return row
    return None


def render_event_hub(event_name: str) -> None:
    """Render the checklist for ``event_name`` (must exist in ``event_hubs.json``)."""
    hub = get_event_hub(event_name)
    if not hub:
        st.error(f"No Event Hub configured for **{event_name}**.")
        st.stop()

    st.session_state["selected_event"] = event_name

    title = hub.get("nav_title") or hub["event_name"]
    st.title(f"🎯 {title}")

    if hub.get("intro"):
        st.markdown(hub["intro"])

    st.warning(
        "Create a trial account using **AI Data Cloud**, not **Cortex Code CLI** — "
        "even if using the CLI in the hands-on lab.",
        icon="⚠️",
    )

    events = load_events()
    trial_url = events.get(hub["event_name"])
    workshop_row = _workshop_row(hub["workshop"])

    st.divider()

    st.subheader("Step 1 — Snowflake trial")
    if trial_url:
        st.markdown("Sign up for a Snowflake trial account for this event.")
        st.link_button("Open Trial Signup", trial_url, type="primary")
    else:
        st.info("Trial signup link coming soon.", icon="🔜")
        st.page_link("pages/1_Trial_Sign_Up.py", label="Check Trial Sign Up", icon="📝")

    st.divider()

    st.subheader("Step 2 — Complete the lab")
    st.markdown(f"Workshop: **{hub['workshop']}**")
    if workshop_row and (workshop_row.get("guide_url") or "").strip():
        st.link_button(
            workshop_row.get("guide_label") or "View Guide",
            workshop_row["guide_url"],
        )
    else:
        st.info("Guide link coming soon.", icon="🔜")
        st.page_link("pages/2_Guides_and_Answer_Keys.py", label="Guides & Answer Keys", icon="📚")

    st.divider()

    st.subheader("Step 3 — Auto-grader & answer key")
    st.markdown(
        "Generate your auto-grader SQL script (same email you used to register), "
        "paste it into a Snowflake worksheet, and run it in full."
    )
    if st.button("Go to Auto-Grader", type="primary", icon="⚙️"):
        st.session_state["auto_grader_workshop_preset"] = hub["workshop"]
        st.switch_page("pages/3_Auto-Grader.py")

    st.divider()

    st.subheader("Badge")
    st.markdown(
        "Complete the lab and run the auto-grader script to qualify for your badge. "
        "Allow **7 business days** after the event; check **Badge status** for updates."
    )
    st.page_link("pages/4_Badge_Status.py", label="Badge status", icon="🏅")
