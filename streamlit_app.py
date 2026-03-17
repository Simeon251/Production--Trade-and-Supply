from __future__ import annotations

import logging

import pandas as pd
import streamlit as st

from src.business_dashboard import BusinessDashboardService

logging.basicConfig(level=logging.INFO, format='%(levelname)s %(name)s: %(message)s')

st.set_page_config(
    page_title='Energy Outlook Navigator',
    page_icon=':bar_chart:',
    layout='wide',
)

SERVICE = BusinessDashboardService()


@st.cache_data(show_spinner='Loading the latest UN energy dataset...')
def load_dashboard_data(data_url: str | None) -> tuple[pd.DataFrame, dict[str, str], str | None]:
    return BusinessDashboardService(data_url).load_data()


def format_number(value: float) -> str:
    return f"{value:,.1f}"


def format_delta(value: float) -> str:
    sign = '+' if value >= 0 else ''
    return f"{sign}{value:.1f}% vs prior period"


def main() -> None:
    st.title('Energy Outlook Navigator')
    st.caption('Business-facing country intelligence and world energy trend monitoring powered by official UN data.')

    with st.sidebar:
        st.header('Controls')
        data_url = st.text_input('Remote data URL override', value='') or None
        forecast_horizon = st.slider('Forecast horizon (years)', min_value=2, max_value=10, value=5)

    df, columns, resolved_source_url = load_dashboard_data(data_url)
    metric_catalog = SERVICE.get_metric_catalog(columns)
    countries = SERVICE.get_countries(df)
    default_country = 'United States of America' if 'United States of America' in countries else countries[0]
    selected_country = st.sidebar.selectbox('Country', countries, index=countries.index(default_country))
    selected_metric = st.sidebar.selectbox('Forecast metric', list(metric_catalog.keys()), index=0)

    world_snapshot = SERVICE.build_world_snapshot(df, columns)
    country_snapshot = SERVICE.build_country_snapshot(df, columns, selected_country)
    world_trend = SERVICE.build_world_trend(df, columns)
    country_trend = SERVICE.build_country_trend(df, selected_country, metric_catalog)
    forecast_df = SERVICE.forecast_country_metric(
        df,
        selected_country,
        selected_metric,
        metric_catalog[selected_metric],
        horizon=forecast_horizon,
    )
    rankings_df = SERVICE.latest_world_rankings(df, world_snapshot['latest_year'], columns)

    st.markdown(f"Source in use: `{resolved_source_url}`")

    overview_tab, country_tab, world_tab = st.tabs(['Executive Overview', 'Country Explorer', 'World Trends'])

    with overview_tab:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric('World Supply', format_number(world_snapshot['world_supply']), format_delta(world_snapshot['world_supply_delta_pct']))
        c2.metric('Average Per-Capita Supply', format_number(world_snapshot['avg_per_capita']))
        c3.metric('Importer Share', f"{world_snapshot['importer_share_pct']:.1f}%")
        c4.metric('Countries Covered', str(world_snapshot['countries_covered']))

        st.subheader('Global Trend Snapshot')
        st.line_chart(world_trend.set_index('Year'))

        st.subheader(f'Top Countries by Total Supply in {world_snapshot["latest_year"]}')
        st.dataframe(rankings_df, use_container_width=True)

    with country_tab:
        k1, k2, k3, k4 = st.columns(4)
        k1.metric('Latest Supply', format_number(country_snapshot['latest_supply']), format_delta(country_snapshot['supply_delta_pct']))
        k2.metric('Per-Capita Supply', format_number(country_snapshot['latest_per_capita']))
        k3.metric('Net Imports', format_number(country_snapshot['latest_net_imports']))
        k4.metric('Trade Position', country_snapshot['importer_status'])

        st.subheader(f'{selected_country} Historical Profile')
        st.line_chart(country_trend.set_index('Year'))

        st.subheader(f'{selected_country} {selected_metric} Outlook')
        st.caption('Forecasts are directional estimates from a simple linear time-trend model and should be treated as planning aids, not certainties.')
        forecast_chart = forecast_df.pivot_table(index='Year', columns='Type', values=selected_metric, aggfunc='first')
        st.line_chart(forecast_chart)
        st.dataframe(forecast_df, use_container_width=True)

    with world_tab:
        st.subheader('World Energy Trend Table')
        st.dataframe(world_trend, use_container_width=True)

        st.subheader(f'Country Ranking Snapshot ({world_snapshot["latest_year"]})')
        ranking_metric = st.selectbox('Ranking metric', ['Total Supply', 'Primary Production', 'Net Imports', 'Per Capita Supply'])
        st.dataframe(rankings_df.sort_values(ranking_metric, ascending=False).reset_index(drop=True), use_container_width=True)


if __name__ == '__main__':
    main()
