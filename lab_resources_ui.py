"""Streamlit UI helpers for lab resource downloads."""

from __future__ import annotations

from typing import Any

import streamlit as st

from lab_resources import find_lab_resource_bundle, mime_type_for_filename, read_lab_file_bytes
from nav_helpers import external_link_button


def render_lab_resources_for_workshop(workshop_title: str, *, key_prefix: str) -> None:
    """Show downloadable lab files when a bundle is configured for ``workshop_title``."""
    bundle = find_lab_resource_bundle(workshop_title)
    if not bundle:
        return

    with st.expander("📦 Lab resources", expanded=False):
        note = (bundle.get("note") or "").strip()
        if note:
            st.caption(note)

        external = bundle.get("external_repo")
        if isinstance(external, dict):
            url = (external.get("url") or "").strip()
            if url:
                external_link_button(
                    external.get("label") or "Open lab repository",
                    url,
                    primary=False,
                    key=f"{key_prefix}_lab_repo",
                )

        groups = bundle.get("groups")
        if not isinstance(groups, list):
            return

        for group_index, group in enumerate(groups):
            if not isinstance(group, dict):
                continue
            title = (group.get("title") or "").strip()
            if title:
                st.markdown(f"**{title}**")

            files = group.get("files")
            if not isinstance(files, list):
                continue

            for file_index, entry in enumerate(files):
                if not isinstance(entry, dict):
                    continue
                name = (entry.get("name") or "").strip()
                rel_path = (entry.get("path") or "").strip()
                help_text = (entry.get("help") or "").strip()
                if not name or not rel_path:
                    continue

                try:
                    data = read_lab_file_bytes(rel_path)
                except (FileNotFoundError, ValueError, OSError):
                    st.warning(f"Lab file unavailable: {name}", icon="⚠️")
                    continue

                col1, col2 = st.columns([1.4, 2])
                with col1:
                    st.download_button(
                        f"Download {name}",
                        data=data,
                        file_name=name,
                        mime=mime_type_for_filename(name),
                        type="secondary",
                        key=f"{key_prefix}_lab_{group_index}_{file_index}",
                    )
                with col2:
                    if help_text:
                        st.caption(help_text)
