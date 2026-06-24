# Event Hub (large events only)

Each configured event gets its **own sidebar label** (e.g. ``Virtual Dev Day (EMEA)``) — not a
generic “Event Hub” item. Pages are listed in ``event_hubs.json`` and appear for all users while
those entries exist (remove after the event if you want them hidden again).

## Configure Virtual Dev Day (EMEA / NOAM)

Edit ``event_hubs.json`` in this repo (commit + push — **not** the Google Sheet):

```json
[
  {
    "event_name": "Virtual Dev Day (EMEA)",
    "nav_title": "Virtual Dev Day (EMEA)",
    "workshop": "Cortex Code Foundations: Getting Started with CoCo",
    "intro": "Optional note for the room."
  },
  {
    "event_name": "Virtual Dev Day (NOAM)",
    "nav_title": "Virtual Dev Day (NOAM)",
    "workshop": "Cortex Code Foundations: Getting Started with CoCo",
    "intro": "Optional note for the room."
  }
]
```

| Field | Required | Notes |
|-------|----------|--------|
| ``event_name`` | Yes | Must match **Event Name** in ``events.json`` exactly |
| ``nav_title`` | No | Sidebar label (defaults to ``event_name``) |
| ``workshop`` | Yes | Must match **Workshop** in ``workshops.json`` (e.g. ``BWCC``) |
| ``intro`` | No | Optional text at top of the hub page |

Add guide and answer key URLs for the workshop on your **Guides & Answer Keys** sheet if needed
(the **Cortex Code Foundations: Getting Started with CoCo** row is already in ``workshops.json``),

## Local preview

```bash
NORTHSTAR_READ_JSON_FROM_DISK=1 streamlit run Home.py
```

Open the sidebar items **Virtual Dev Day (EMEA)** or **Virtual Dev Day (NOAM)** directly.

## Slide links

Send each region to a mirror URL; attendees open their labeled sidebar page:

```
https://northstar3.streamlit.app/
```

(EMEA and NOAM each have their own sidebar entry — no ``?event=`` required, but deep links still work.)
