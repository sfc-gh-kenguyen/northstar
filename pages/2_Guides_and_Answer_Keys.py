import streamlit as st

from workshops import load_workshop_rows


def _md_cell(text: str) -> str:
    """Escape pipe characters so markdown table cells stay valid."""
    return (text or "").replace("|", "\\|")

st.title("📚 Workshop Guides and Answer Keys")

rows = load_workshop_rows()
if not rows:
    st.info(
        "No workshops are configured yet. Add a **Guides & Answer Keys** tab to your Google Sheet "
        "(see column headers below), set **SHEET_GUIDES** in Apps Script to that tab’s name, then run "
        "**GitHub Sync → Push events & guides to GitHub**, or edit **workshops.json** in this repository.",
        icon="ℹ️",
    )
    st.markdown(
        """
**Sheet tab (when using sync):** create a tab (e.g. `Guides & Answer Keys`) and set `SHEET_GUIDES` in Apps Script to match its name.

| Column | Required |
|--------|----------|
| **Workshop** (or **Course name** / **Title**) | Yes — full title (must match Auto-Grader once an answer key exists) |
| **Guide URL** | No — leave blank for **Coming soon** in the Guide column |
| **Answer Key URL** | No — leave blank until the script is ready (**Coming soon** on the page; row stays out of the Auto-Grader list until filled) |
| **Guide link text** | No — link label when Guide URL is set (default `View Guide`) |
| **Answer Key link text** | No — link label when Answer Key URL is set (default: file name from URL) |
| **Guide placeholder** | No — overrides *Coming soon* when Guide URL is empty |
| **Answer Key placeholder** | No — overrides *Coming soon* when Answer Key URL is empty |
        """.strip()
    )
    st.stop()

lines = ["| Workshop | Guide | Answer Key |", "|----------|-------|------------|"]
for r in rows:
    w = _md_cell(r["workshop"])
    if (r.get("guide_url") or "").strip():
        g = f"[{r['guide_label']}]({r['guide_url']})"
    else:
        g = _md_cell(r.get("guide_pending_text") or "Coming soon")
    if (r.get("answer_key_url") or "").strip():
        a = f"[{r['answer_key_label']}]({r['answer_key_url']})"
    else:
        a = _md_cell(r.get("answer_key_pending_text") or "Coming soon")
    lines.append(f"| {w} | {g} | {a} |")

st.markdown("\n".join(lines))
