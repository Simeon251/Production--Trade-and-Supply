from __future__ import annotations

import logging

import pandas as pd
import streamlit as st

from src.business_dashboard import BusinessDashboardService, WORLD_ENTITY_NAME

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

st.set_page_config(
    page_title="Energy Outlook Navigator",
    page_icon=":bar_chart:",
    layout="wide",
)

SERVICE = BusinessDashboardService()


@st.cache_data(show_spinner="Loading the latest UN energy dataset...")
def load_dashboard_data() -> tuple[pd.DataFrame, dict[str, str], str | None]:
    return SERVICE.load_data()


def format_number(value: float) -> str:
    return f"{value:,.1f}"


def format_delta(value: float) -> str:
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.1f}% vs prior period"


def main() -> None:
    st.title("Energy Outlook Navigator")
    st.caption(
        "Business-facing country intelligence and world energy trend monitoring powered by official UN data."
    )

    df, columns, resolved_source_url = load_dashboard_data()
    metric_catalog = SERVICE.get_metric_catalog(columns)
    countries = SERVICE.get_entities(df, "Country")
    aggregate_regions = SERVICE.get_entities(df, "Aggregate Region")

    with st.sidebar:
        st.header("Controls")
        entity_mode = st.radio("Explore", ["Country", "Aggregate Region", "World"], index=0)
        forecast_horizon = st.slider("Forecast horizon (years)", min_value=2, max_value=10, value=5)
        selected_metric = st.selectbox("Forecast metric", list(metric_catalog.keys()), index=0)

        if entity_mode == "Country":
            default_country = "United States of America" if "United States of America" in countries else countries[0]
            selected_entity = st.selectbox("Country", countries, index=countries.index(default_country))
        elif entity_mode == "Aggregate Region":
            selected_entity = st.selectbox("Aggregate Region", aggregate_regions, index=0)
        else:
            selected_entity = WORLD_ENTITY_NAME
            st.caption("World mode uses the explicit UN world total, not a double-counted sum.")

    world_snapshot = SERVICE.build_world_snapshot(df, columns)
    entity_snapshot = SERVICE.build_entity_snapshot(df, columns, selected_entity)
    world_trend = SERVICE.build_world_trend(df, columns)
    entity_trend = SERVICE.build_entity_trend(df, selected_entity, metric_catalog)
    forecast_df = SERVICE.forecast_entity_metric(
        df,
        selected_entity,
        selected_metric,
        metric_catalog[selected_metric],
        horizon=forecast_horizon,
    )
    rankings_df = SERVICE.latest_country_rankings(df, world_snapshot["latest_year"], columns)

    st.markdown(f"Source in use: `{resolved_source_url}`")
    st.markdown(
        f"Current view: **{entity_mode}** | Forecast horizon: **{forecast_horizon} years** | Forecast metric: **{selected_metric}**"
    )

    overview_tab, entity_tab, world_tab = st.tabs(["Executive Overview", "Entity Explorer", "World Trends"])

    with overview_tab:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("World Supply", format_number(world_snapshot["world_supply"]), format_delta(world_snapshot["world_supply_delta_pct"]))
        c2.metric("Average Per-Capita Supply", format_number(world_snapshot["avg_per_capita"]))
        c3.metric("Importer Share", f"{world_snapshot['importer_share_pct']:.1f}%")
        c4.metric("Countries Covered", str(world_snapshot["countries_covered"]))

        st.subheader("Global Trend Snapshot")
        st.line_chart(world_trend.set_index("Year"))

        st.subheader(f"Top Countries by Total Supply in {world_snapshot['latest_year']}")
        st.dataframe(rankings_df, use_container_width=True)

    with entity_tab:
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Latest Supply", format_number(entity_snapshot["latest_supply"]), format_delta(entity_snapshot["supply_delta_pct"]))
        k2.metric("Per-Capita Supply", format_number(entity_snapshot["latest_per_capita"]))
        k3.metric("Net Imports", format_number(entity_snapshot["latest_net_imports"]))
        k4.metric("Trade Position", entity_snapshot["trade_position"])

        st.subheader(f"{selected_entity} Historical Profile")
        st.line_chart(entity_trend.set_index("Year"))

        st.subheader(f"{selected_entity} {selected_metric} Outlook")
        st.caption(
            "Forecasts are directional estimates from a simple linear time-trend model and should be treated as planning aids, not certainties."
        )
        st.caption(f"Forecast extends through {int(forecast_df['Year'].max())}.")
        forecast_chart = forecast_df.pivot_table(index="Year", columns="Type", values=selected_metric, aggfunc="first")
        st.line_chart(forecast_chart)
        st.dataframe(forecast_df, use_container_width=True)

    with world_tab:
        st.subheader("World Energy Trend Table")
        st.dataframe(world_trend, use_container_width=True)

        st.subheader(f"Country Ranking Snapshot ({world_snapshot['latest_year']})")
        ranking_metric = st.selectbox("Ranking metric", ["Total Supply", "Primary Production", "Net Imports", "Per Capita Supply"])
        st.dataframe(rankings_df.sort_values(ranking_metric, ascending=False).reset_index(drop=True), use_container_width=True)


if __name__ == "__main__":
    main()
