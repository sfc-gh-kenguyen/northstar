import streamlit as st

from events import load_events

EVENTS = load_events()
EVENT_OPTIONS = ["None"] + list(EVENTS.keys())

st.title("📝 Trial Sign Up")


def _sync_event_query_param() -> None:
    ev = st.session_state.get("selected_event", "None")
    if ev and ev != "None":
        st.query_params["event"] = ev
    else:
        try:
            del st.query_params["event"]
        except KeyError:
            pass


st.selectbox(
    "Select your event",
    EVENT_OPTIONS,
    key="selected_event",
    on_change=_sync_event_query_param,
)

event = st.session_state["selected_event"]
if not event or event == "None":
    st.info("Choose your event above to see your trial signup link.", icon="ℹ️")
    st.stop()

link = EVENTS.get(event)
if link:
    st.markdown(f"Sign up for a Snowflake trial account for **{event}**:")
    st.link_button("Open Trial Signup", link)
else:
    st.markdown(f"**{event}**")
    st.info("Link coming soon.", icon="🔜")
