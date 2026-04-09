import streamlit as st
from events import load_events

st.set_page_config(page_title="Snowflake Northstar", page_icon="❄️", layout="wide")

EVENTS = load_events()
EVENT_OPTIONS = ["None"] + list(EVENTS.keys())

if "selected_event" not in st.session_state:
    st.session_state.selected_event = "None"

_idx = EVENT_OPTIONS.index(st.session_state.selected_event) if st.session_state.selected_event in EVENT_OPTIONS else 0

with st.sidebar:
    chosen = st.selectbox("Select your event", EVENT_OPTIONS, index=_idx)
    st.session_state.selected_event = chosen

pages = [
    st.Page("home_page.py", title="Home", icon="❄️", default=True),
    st.Page("pages/1_Trial_Sign_Up.py", title="Trial Sign Up", icon="📝"),
    st.Page("pages/2_Auto-Grader_Answer_Key.py", title="Auto-Grader/Answer Key", icon="⚙️"),
]

nav = st.navigation(pages)
nav.run()
