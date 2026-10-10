# Copyright 2026 Snowflake Inc.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from datetime import timedelta

import altair as alt
import pandas as pd
import streamlit as st

st.set_page_config(layout="wide")

# Cell colors by how many campaigns are live for the same audience on the same day.
HEAT_COLORS = {"1": "#eceff3", "2": "#f39c4a", "3+": "#d62728"}

conn = st.connection("snowflake")


@st.cache_data(ttl=300)
def load_campaigns() -> pd.DataFrame:
    df = conn.query(
        """
        SELECT campaign_id, campaign_name, channel, region, audience,
               start_date, end_date, budget_usd, owner_team
        FROM MERIDIAN_STAY.CURATED.CAMPAIGNS
        ORDER BY region, audience, start_date
        """
    )
    df.columns = [c.lower() for c in df.columns]
    df["start_date"] = pd.to_datetime(df["start_date"])
    df["end_date"] = pd.to_datetime(df["end_date"])
    # CRM-only campaigns have no owner team in the source data.
    df["owner_team"] = df["owner_team"].replace("", None).fillna("Unassigned")
    df["lane"] = df["region"] + " · " + df["audience"]
    return df


def week_start(day: pd.Timestamp) -> pd.Timestamp:
    """Weeks start on Sunday."""
    return day - timedelta(days=(day.dayofweek + 1) % 7)


def daily_live(df: pd.DataFrame) -> pd.DataFrame:
    """One row per campaign per day it is live."""
    days = [
        (row.lane, day, row.campaign_name, row.owner_team)
        for row in df.itertuples()
        for day in pd.date_range(row.start_date, row.end_date)
    ]
    daily = pd.DataFrame(days, columns=["lane", "day", "campaign", "team"])
    daily["week"] = daily["day"].map(week_start)
    return daily


def weekly_heat(daily: pd.DataFrame) -> pd.DataFrame:
    """One row per audience and week: the most campaigns live on any single day, and who was running."""
    peak = (
        daily.groupby(["lane", "week", "day"]).size()
        .groupby(["lane", "week"]).max()
        .rename("peak")
    )
    running = (
        daily.assign(who=daily["campaign"] + " (" + daily["team"] + ")")
        .drop_duplicates(["lane", "week", "who"])
        .groupby(["lane", "week"])["who"]
        .agg(lambda c: " · ".join(sorted(c)))
        .rename("campaigns")
    )
    heat = pd.concat([peak, running], axis=1).reset_index()
    heat["level"] = heat["peak"].map(lambda p: "3+" if p >= 3 else str(p))
    heat["week_key"] = heat["week"].dt.strftime("%Y-%m-%d")
    heat["week_label"] = heat["week"].dt.strftime("%b %-d")
    return heat


def week_axis_labels(weeks: list[pd.Timestamp]) -> str:
    """Vega expression that shows the month name on the first week of each month and the day number elsewhere."""
    labels, last_month = {}, None
    for w in weeks:
        labels[w.strftime("%Y-%m-%d")] = w.strftime("%b %-d") if w.month != last_month else w.strftime("%-d")
        last_month = w.month
    pairs = ", ".join(f"'{k}': '{v}'" for k, v in labels.items())
    return f"{{{pairs}}}[datum.value]"


def heatmap(heat: pd.DataFrame, lanes: list[str], weeks: list[pd.Timestamp]) -> alt.Chart:
    """Weeks are the whole season, so the axis stays the same when you filter to one region."""
    base = alt.Chart(heat[heat["lane"].isin(lanes)]).encode(
        x=alt.X(
            "week_key:O",
            title=None,
            sort=[w.strftime("%Y-%m-%d") for w in weeks],
            scale=alt.Scale(domain=[w.strftime("%Y-%m-%d") for w in weeks]),
            axis=alt.Axis(labelAngle=0, labelExpr=week_axis_labels(weeks), labelFontSize=12, orient="top", ticks=False, domain=False),
        ),
        y=alt.Y("lane:N", title=None, sort=lanes, axis=alt.Axis(labelLimit=320, labelFontSize=13, labelColor="#1f2a37", ticks=False, domain=False)),
    )
    cells = base.mark_rect(cornerRadius=4, stroke="white", strokeWidth=3).encode(
        color=alt.Color(
            "level:N",
            title="Live at once",
            scale=alt.Scale(domain=list(HEAT_COLORS), range=list(HEAT_COLORS.values())),
            legend=alt.Legend(orient="bottom", direction="horizontal", titleFontSize=12, labelFontSize=12),
        ),
        tooltip=[
            alt.Tooltip("lane:N", title="Region · audience"),
            alt.Tooltip("week_label:N", title="Week of"),
            alt.Tooltip("peak:Q", title="Live at once"),
            alt.Tooltip("campaigns:N", title="Running that week (owner)"),
        ],
    )
    # Only the hot cells get a number, so they're the only thing that stands out.
    labels = base.transform_filter("datum.peak >= 2").mark_text(fontSize=14, fontWeight="bold", color="white").encode(text="peak:Q")
    return (cells + labels).properties(height={"step": 44})


st.title("Meridian Stay: where are we hitting the same people twice?")
st.caption(
    "Every campaign from the ad platforms, the email & SMS platform, and the CRM, November 2026 through January 2027. "
    "Each row is a region and audience; each column is a week. Orange and red cells mean the same people are "
    "getting competing offers on the same days. Hover over a cell to see who's running."
)

campaigns = load_campaigns()
season_weeks = list(pd.date_range(
    week_start(campaigns["start_date"].min()), week_start(campaigns["end_date"].max()), freq="7D"
))
f1, f2 = st.columns([1, 3], vertical_alignment="bottom")
region = f1.selectbox("Region", ["All regions"] + sorted(campaigns["region"].unique()))
show_all = f2.toggle("Show all audiences", value=False, help="By default, only audiences with competing offers are shown.")
if region != "All regions":
    campaigns = campaigns[campaigns["region"] == region]

daily = daily_live(campaigns)
heat = weekly_heat(daily)

peak_by_lane = heat.groupby("lane")["peak"].max()
colliding = peak_by_lane[peak_by_lane >= 2]
order = (
    peak_by_lane.reset_index()
    .sort_values(["peak", "lane"], ascending=[False, True])["lane"]
    .tolist()
)

m1, m2, m3 = st.columns(3)
m1.metric("Region · audience pairs with competing offers", f"{len(colliding)} of {len(peak_by_lane)}")
if colliding.empty:
    m2.metric("Most campaigns at once", "1")
    m2.caption("No audience gets more than one campaign at a time.")
else:
    # The busiest audience in scope, the teams live on its busiest day, and the weeks it peaks.
    top = heat.sort_values(["peak", "week"], ascending=[False, True]).iloc[0]
    top_days = daily[daily["lane"] == top["lane"]]
    busiest_day = top_days.groupby("day").size().idxmax()
    owners = top_days.loc[top_days["day"] == busiest_day, "team"]
    teams = sorted(owners[owners != "Unassigned"].unique())
    unassigned = int((owners == "Unassigned").sum())
    peak_weeks = heat.loc[(heat["lane"] == top["lane"]) & (heat["peak"] == top["peak"]), "week"]
    m2.metric("Most campaigns at once", f"{top['peak']}")
    owner_note = f"{len(teams)} {'team' if len(teams) == 1 else 'teams'}: {', '.join(teams)}" if teams else "no owner team"
    if teams and unassigned:
        owner_note += f" + {unassigned} unassigned"
    m2.caption(f"{top['lane']} · {owner_note}")
    m3.metric("Peak weeks", f"{peak_weeks.min():%b %-d} – {peak_weeks.max() + timedelta(days=6):%b %-d}")
    m3.caption(top["lane"])

lanes = order if show_all else [lane for lane in order if lane in colliding.index]
if not lanes:
    st.info("No competing offers here. Turn on **Show all audiences** to see every campaign.")

st.altair_chart(heatmap(heat, lanes, season_weeks), width="stretch")

st.subheader("Inspect an audience")
selected_lane = st.selectbox("Region · audience", order)
st.dataframe(
    campaigns.loc[
        campaigns["lane"] == selected_lane,
        ["campaign_name", "owner_team", "channel", "start_date", "end_date", "budget_usd"],
    ].assign(
        start_date=lambda d: d["start_date"].dt.date,
        end_date=lambda d: d["end_date"].dt.date,
        budget_usd=lambda d: d["budget_usd"].map("${:,.0f}".format),
    ),
    hide_index=True,
    width="stretch",
)
