"""Load ``events.json`` / ``workshops.json`` from GitHub when hosted on Streamlit Cloud.

Community Cloud can serve an older git checkout in the container until reboot; fetching
``raw.githubusercontent.com`` always reflects the latest commit on ``main`` after sheet sync.
"""

from __future__ import annotations

import os
import pathlib
import urllib.error
import urllib.request

_ROOT = pathlib.Path(__file__).resolve().parent

# Keep in sync with apps_script.js REPO_OWNER / REPO_NAME / BRANCH
_DEFAULT_OWNER = "sfc-gh-kenguyen"
_DEFAULT_REPO = "northstar"
_DEFAULT_BRANCH = "main"


def _raw_base_url() -> str | None:
    """Base URL without trailing slash, or None to read from disk only."""
    env = os.environ.get("NORTHSTAR_JSON_RAW_BASE", "").strip().rstrip("/")
    if env:
        return env
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
    except Exception:
        return None
    if get_script_run_ctx() is None:
        return None
    try:
        import streamlit as st

        try:
            v = st.secrets["NORTHSTAR_JSON_RAW_BASE"]
            if v:
                return str(v).strip().rstrip("/")
        except Exception:
            pass
        host = (st.context.headers.get("Host") or st.context.headers.get("host") or "").lower()
        if ".streamlit.app" in host or ".streamlit.cloud" in host:
            return (
                f"https://raw.githubusercontent.com/"
                f"{_DEFAULT_OWNER}/{_DEFAULT_REPO}/{_DEFAULT_BRANCH}"
            )
    except Exception:
        pass
    return None


def read_repo_json(relative_path: str) -> str:
    """Return file text. Hosted Streamlit: GitHub raw ``main``; local dev: repo copy on disk."""
    if os.environ.get("NORTHSTAR_READ_JSON_FROM_DISK", "").lower() in ("1", "true", "yes"):
        return (_ROOT / relative_path).read_text(encoding="utf-8")

    base = _raw_base_url()
    if base:
        url = f"{base}/{relative_path}"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "northstar-streamlit-json",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
            },
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                return resp.read().decode("utf-8")
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
            pass

    return (_ROOT / relative_path).read_text(encoding="utf-8")
