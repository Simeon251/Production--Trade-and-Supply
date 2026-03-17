from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from .data_processor import DataProcessor
from .feature_engineer import FeatureEngineer


@dataclass
class BusinessDashboardService:
    """Prepare current-state, trend, and forecast views for the Streamlit app."""

    data_url: str | None = None

    def load_data(self) -> tuple[pd.DataFrame, dict[str, str], str | None]:
        processor = DataProcessor(self.data_url)
        processor.load_data()
        wide_df = processor.clean()

        engineer = FeatureEngineer(wide_df)
        enriched_df = engineer.create_features()
        columns = engineer._detect_columns()
        resolved = processor.resolved_source_url
        return enriched_df, {key: value for key, value in columns.items() if value is not None}, resolved

    @staticmethod
    def get_countries(df: pd.DataFrame) -> list[str]:
        return sorted(df['Region'].dropna().unique().tolist())

    @staticmethod
    def get_latest_year(df: pd.DataFrame) -> int:
        return int(df['Year'].max())

    @staticmethod
    def get_metric_catalog(columns: dict[str, str]) -> dict[str, str]:
        return {
            'Total Supply': columns['supply'],
            'Primary Production': columns['prod'],
            'Net Imports': columns['netimp'],
            'Stock Changes': columns.get('stock', columns['netimp']),
            'Per Capita Supply': columns['percap'],
        }

    def build_country_snapshot(self, df: pd.DataFrame, columns: dict[str, str], country: str) -> dict[str, Any]:
        country_df = df[df['Region'] == country].sort_values('Year')
        latest = country_df.iloc[-1]
        previous = country_df.iloc[-2] if len(country_df) > 1 else latest

        latest_supply = float(latest[columns['supply']])
        previous_supply = float(previous[columns['supply']])
        latest_percap = float(latest[columns['percap']])
        latest_net_imports = float(latest[columns['netimp']])
        importer_status = 'Net Importer' if latest_net_imports > 0 else 'Net Exporter'

        return {
            'country': country,
            'latest_year': int(latest['Year']),
            'latest_supply': latest_supply,
            'supply_delta_pct': self._pct_change(previous_supply, latest_supply),
            'latest_per_capita': latest_percap,
            'latest_net_imports': latest_net_imports,
            'importer_status': importer_status,
            'production': float(latest[columns['prod']]),
        }

    @staticmethod
    def build_country_trend(df: pd.DataFrame, country: str, metric_columns: dict[str, str]) -> pd.DataFrame:
        country_df = df[df['Region'] == country].sort_values('Year').copy()
        trend_df = pd.DataFrame({'Year': country_df['Year'].astype(int)})
        for label, column in metric_columns.items():
            trend_df[label] = country_df[column].astype(float).values
        return trend_df

    @staticmethod
    def build_world_trend(df: pd.DataFrame, columns: dict[str, str]) -> pd.DataFrame:
        grouped = df.groupby('Year', as_index=False).agg(
            total_supply=(columns['supply'], 'sum'),
            total_production=(columns['prod'], 'sum'),
            total_net_imports=(columns['netimp'], 'sum'),
            avg_per_capita=(columns['percap'], 'mean'),
        )
        grouped = grouped.rename(
            columns={
                'Year': 'Year',
                'total_supply': 'World Total Supply',
                'total_production': 'World Production',
                'total_net_imports': 'World Net Imports',
                'avg_per_capita': 'Average Per Capita Supply',
            }
        )
        return grouped.sort_values('Year').reset_index(drop=True)

    @staticmethod
    def latest_world_rankings(df: pd.DataFrame, year: int, columns: dict[str, str], top_n: int = 10) -> pd.DataFrame:
        latest_df = df[df['Year'] == year][['Region', columns['supply'], columns['prod'], columns['netimp'], columns['percap']]].copy()
        latest_df = latest_df.rename(
            columns={
                columns['supply']: 'Total Supply',
                columns['prod']: 'Primary Production',
                columns['netimp']: 'Net Imports',
                columns['percap']: 'Per Capita Supply',
            }
        )
        return latest_df.sort_values('Total Supply', ascending=False).head(top_n).reset_index(drop=True)

    @staticmethod
    def forecast_country_metric(df: pd.DataFrame, country: str, metric_label: str, metric_column: str, horizon: int = 3) -> pd.DataFrame:
        country_df = df[df['Region'] == country].sort_values('Year')
        history = country_df[['Year', metric_column]].dropna().copy()
        history['Year'] = history['Year'].astype(int)
        history[metric_label] = history[metric_column].astype(float)
        history = history[['Year', metric_label]]
        history['Type'] = 'Historical'

        if len(history) < 3:
            return history

        future_years = np.arange(history['Year'].max() + 1, history['Year'].max() + horizon + 1)
        coefficients = np.polyfit(history['Year'].to_numpy(), history[metric_label].to_numpy(), deg=1)
        forecast_values = np.polyval(coefficients, future_years)
        forecast_df = pd.DataFrame({
            'Year': future_years,
            metric_label: forecast_values,
            'Type': 'Forecast',
        })
        return pd.concat([history, forecast_df], ignore_index=True)

    @staticmethod
    def build_world_snapshot(df: pd.DataFrame, columns: dict[str, str]) -> dict[str, Any]:
        latest_year = int(df['Year'].max())
        previous_year = int(sorted(df['Year'].unique())[-2]) if df['Year'].nunique() > 1 else latest_year
        latest_df = df[df['Year'] == latest_year]
        previous_df = df[df['Year'] == previous_year]

        latest_supply = float(latest_df[columns['supply']].sum())
        previous_supply = float(previous_df[columns['supply']].sum())
        avg_per_capita = float(latest_df[columns['percap']].mean())
        importer_share = float((latest_df['is_importer'].mean()) * 100)

        return {
            'latest_year': latest_year,
            'world_supply': latest_supply,
            'world_supply_delta_pct': BusinessDashboardService._pct_change(previous_supply, latest_supply),
            'avg_per_capita': avg_per_capita,
            'importer_share_pct': importer_share,
            'countries_covered': int(latest_df['Region'].nunique()),
        }

    @staticmethod
    def _pct_change(previous: float, current: float) -> float:
        if previous == 0:
            return 0.0
        return ((current - previous) / abs(previous)) * 100.0
