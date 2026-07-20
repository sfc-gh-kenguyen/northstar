# Event Hub (large events only)

Configured events get **richer content on Event Page** and may also appear as **dedicated
sidebar items** for large events (e.g. Pune multi-track day). Add entries to
``event_hubs.json`` (commit + push — **not** the Google Sheet) before a big event.
Remove entries (or set the file to ``[]``) after the event.

## How event → workshop mapping works

| Data | Source | What it provides |
|------|--------|------------------|
| **Event name + trial URL** | Events Google Sheet → ``events.json`` | Trial signup link |
| **Workshop for an event** | Events sheet **Workshop** column → ``events.json`` | One lab per row (use ``;`` for two parallel labs) |
| **Workshop + guide URLs** | Guides sheet → ``workshops.json`` | Lab guides and answer keys |
| **Multi-track big events** | ``event_hubs.json`` in this repo | Overrides sheet when configured (sidebar + richer copy) |

Most events only need the **Workshop** column on the Events sheet. Use ``event_hubs.json`` for
large virtual events that need dedicated sidebar pages or custom intro text.

## Configure Pune (July 2026)

```json
[
  {
    "event_name": "Pune (7/25/2026)",
    "nav_title": "Pune (7/25/2026)",
    "page": "pages/5_Pune.py",
    "workshops": [
      "CoCo Foundations: Getting Started with CoCo",
      "Building AI Applications with Snowflake Cortex: RAG, Text-to-SQL & CoCo",
      "From Zero to Agents: Building End-to-End Data Pipeline for an AI Agent",
      "Build an End-to-End Application Using CoCo on Snowflake",
      "Building Intelligence Data Application with Snowflake CoWork",
      "Data Ingestion, Transformation, and Delivery with Snowflake",
      "Creating Declarative Data Pipelines with Dynamic Tables"
    ],
    "intro": "Follow the steps below in order. Use the same email for trial signup and the auto-grader."
  }
]
```

| Field | Required | Notes |
|-------|----------|--------|
| ``event_name`` | Yes | Must match **Event Name** in ``events.json`` exactly |
| ``nav_title`` | No | Heading on Event Page (defaults to ``event_name``) |
| ``workshop`` | One of | Single lab — use for one-workshop events |
| ``workshops`` | One of | List of lab names for multi-track days (must match ``workshops.json``) |
| ``trial_events`` | No | Extra trial signup event names (defaults to ``event_name`` only) |
| ``intro`` | No | Optional text below the event heading |

Guide and answer key URLs come from ``workshops.json`` (Guides & Answer Keys sheet).

## Attendee flow

**Large events (Pune):** open **Pune (7/25/2026)** in the sidebar,
or use **Event Page** and pick the same event from the dropdown.

**Other events:** open **Event Page**, select the event, follow the checklist.

Deep links still work: ``?event=Pune%20(7%2F25%2F2026)``

## All mirrors must redeploy

After pushing ``event_hubs.json`` changes, reboot every mirror you use on slides and
verify in incognito. See [TRAFFIC_SPLITTING.md](TRAFFIC_SPLITTING.md).

## Local preview

```bash
git pull origin main   # pick up sheet-synced events.json if needed
NORTHSTAR_READ_JSON_FROM_DISK=1 python3 -m streamlit run Home.py
```

Open **Event Page** and select **Pune (7/25/2026)**.

## After the event

Set ``event_hubs.json`` to ``[]``, commit, push, and reboot mirrors.
