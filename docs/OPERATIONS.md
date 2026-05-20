# Northstar — operations

## Streamlit entrypoints

| Main file | Purpose |
|-----------|---------|
| `Home.py` | Primary Northstar app: `st.navigation`, sheet-driven JSON, all features. **Use this** for the main Community Cloud deployment. |
| `LegacyAutograderRedirect.py` | Only for a **separate** Streamlit app still bound to the legacy hostname `northstarautograder.streamlit.app`. It redirects browsers to the canonical `northstar.streamlit.app` (and preserves path/query). **Do not** set this as the main app’s entry if you want the full product. |
| `home_page.py` | Loaded as a **page** by `Home.py`, not run alone on Community Cloud (except backup / local experiments noted in code comments). |

After changing entrypoints, confirm each Community Cloud app’s **main file** in the deploy UI matches the row above.

## GitHub and sheet sync

- **Source of truth for repo coordinates:** `deploy.json` at the repository root (`github.owner`, `github.repo`, `github.branch`).
- **Python / Streamlit:** `deploy_config.py` and `repo_json.py` read `deploy.json` (with sensible defaults if the file is missing).
- **Google Apps Script (`apps_script.js`):** On each push, the script loads `deploy.json` from **raw GitHub** using `NORTHSTAR_DEPLOY_JSON_URL` (bootstrap URL). If that fetch fails, it falls back to `REPO_FALLBACK_*` constants — **keep those aligned with `deploy.json`** when you fork or rename the repo.
- When you **fork** or move the repo, update: `deploy.json`, `NORTHSTAR_DEPLOY_JSON_URL` in Apps Script, and the fallback constants in one pass.

## Data files (`events.json`, `workshops.json`)

- Updated by **Apps Script → GitHub Contents API** (see `apps_script.js`).
- The hosted app prefers **raw.githubusercontent.com** (see `repo_json.py`) so JSON changes do not depend on the container’s git checkout staying fresh.

## Fresh JSON after sheet sync (no reboot)

- The app loads ``events.json`` / ``workshops.json`` from **raw.githubusercontent.com** whenever it detects Streamlit Community Cloud (host contains ``.streamlit.app`` or ``.streamlit.cloud``), so updates are **not** tied to the container’s git checkout.
- JSON is **cached per commit SHA**: the app checks branch HEAD occasionally (default every 5 minutes per browser session), not on every widget rerun. After **GitHub Sync → Push**, use sidebar **Refresh event & workshop data** (or wait for the next SHA check) to pick up changes immediately.
- Optional Streamlit secret ``NORTHSTAR_GITHUB_TOKEN`` (or env ``GITHUB_TOKEN``): GitHub PAT with ``public_repo`` (or repo scope) raises API rate limits for SHA checks during busy events.
- Env ``NORTHSTAR_SHA_CHECK_INTERVAL_SEC`` (default ``300``): seconds between automatic branch HEAD checks.
- If the app URL is a **custom domain** that does **not** include ``.streamlit.app``, set either:
  - ``NORTHSTAR_JSON_RAW_BASE`` in **Secrets** to  
    ``https://raw.githubusercontent.com/<owner>/<repo>/<branch>`` (no trailing slash), or  
  - ``NORTHSTAR_FORCE_RAW_JSON`` = ``true`` to use the same raw base as ``deploy.json`` without relying on the hostname.

## Local development

- Install: `pip install -r requirements.txt`
- Tests: `pip install -r requirements-dev.txt` then `pytest`
- To force disk-only JSON (no remote fetch): set environment variable `NORTHSTAR_READ_JSON_FROM_DISK=1`.
