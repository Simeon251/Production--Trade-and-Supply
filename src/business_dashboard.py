from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from .data_processor import DataProcessor
from .feature_engineer import FeatureEngineer

WORLD_ENTITY_NAME = "Total, all countries or areas"
AGGREGATE_REGION_NAMES = {
    "Africa",
    "Asia",
    "Europe",
    "Latin America & the Caribbean",
    "Northern America",
    "Oceania",
    WORLD_ENTITY_NAME,
}


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
        enriched_df["Entity Type"] = enriched_df["Region"].map(self.classify_entity)
        columns = engineer._detect_columns()
        resolved = processor.resolved_source_url
        return enriched_df, {key: value for key, value in columns.items() if value is not None}, resolved

    @staticmethod
    def classify_entity(name: str) -> str:
        if name == WORLD_ENTITY_NAME:
            return "World"
        if name in AGGREGATE_REGION_NAMES:
            return "Aggregate Region"
        return "Country"

    def get_entities(self, df: pd.DataFrame, entity_type: str) -> list[str]:
        filtered = df[df["Entity Type"] == entity_type]
        return sorted(filtered["Region"].dropna().unique().tolist())

    @staticmethod
    def get_latest_year(df: pd.DataFrame) -> int:
        return int(df["Year"].max())

    @staticmethod
    def get_metric_catalog(columns: dict[str, str]) -> dict[str, str]:
        return {
            "Total Supply": columns["supply"],
            "Primary Production": columns["prod"],
            "Net Imports": columns["netimp"],
            "Stock Changes": columns.get("stock", columns["netimp"]),
            "Per Capita Supply": columns["percap"],
        }

    def build_entity_snapshot(
        self,
        df: pd.DataFrame,
        columns: dict[str, str],
        entity_name: str,
    ) -> dict[str, Any]:
        entity_df = df[df["Region"] == entity_name].sort_values("Year")
        latest = entity_df.iloc[-1]
        previous = entity_df.iloc[-2] if len(entity_df) > 1 else latest

        latest_supply = float(latest[columns["supply"]])
        previous_supply = float(previous[columns["supply"]])
        latest_percap = float(latest[columns["percap"]])
        latest_net_imports = float(latest[columns["netimp"]])
        importer_status = "Net Importer" if latest_net_imports > 0 else "Net Exporter"

        return {
            "entity": entity_name,
            "entity_type": str(latest["Entity Type"]),
            "latest_year": int(latest["Year"]),
            "latest_supply": latest_supply,
            "supply_delta_pct": self._pct_change(previous_supply, latest_supply),
            "latest_per_capita": latest_percap,
            "latest_net_imports": latest_net_imports,
            "trade_position": importer_status,
            "production": float(latest[columns["prod"]]),
        }

    @staticmethod
    def build_entity_trend(df: pd.DataFrame, entity_name: str, metric_columns: dict[str, str]) -> pd.DataFrame:
        entity_df = df[df["Region"] == entity_name].sort_values("Year").copy()
        trend_df = pd.DataFrame({"Year": entity_df["Year"].astype(int)})
        for label, column in metric_columns.items():
            trend_df[label] = entity_df[column].astype(float).values
        return trend_df

    @staticmethod
    def build_world_trend(df: pd.DataFrame, columns: dict[str, str]) -> pd.DataFrame:
        world_df = df[df["Region"] == WORLD_ENTITY_NAME].sort_values("Year").copy()
        return pd.DataFrame(
            {
                "Year": world_df["Year"].astype(int),
                "World Total Supply": world_df[columns["supply"]].astype(float).values,
                "World Production": world_df[columns["prod"]].astype(float).values,
                "World Net Imports": world_df[columns["netimp"]].astype(float).values,
                "Average Per Capita Supply": world_df[columns["percap"]].astype(float).values,
            }
        )

    def latest_country_rankings(
        self,
        df: pd.DataFrame,
        year: int,
        columns: dict[str, str],
        top_n: int = 10,
    ) -> pd.DataFrame:
        latest_df = df[(df["Year"] == year) & (df["Entity Type"] == "Country")][
            ["Region", columns["supply"], columns["prod"], columns["netimp"], columns["percap"]]
        ].copy()
        latest_df = latest_df.rename(
            columns={
                columns["supply"]: "Total Supply",
                columns["prod"]: "Primary Production",
                columns["netimp"]: "Net Imports",
                columns["percap"]: "Per Capita Supply",
            }
        )
        return latest_df.sort_values("Total Supply", ascending=False).head(top_n).reset_index(drop=True)

    def forecast_entity_metric(
        self,
        df: pd.DataFrame,
        entity_name: str,
        metric_label: str,
        metric_column: str,
        horizon: int = 3,
    ) -> pd.DataFrame:
        entity_df = df[df["Region"] == entity_name].sort_values("Year")
        history = entity_df[["Year", metric_column]].dropna().copy()
        history["Year"] = history["Year"].astype(int)
        history[metric_label] = history[metric_column].astype(float)
        history = history[["Year", metric_label]]
        history["Type"] = "Historical"

        if len(history) < 3:
            return history

        future_years = np.arange(history["Year"].max() + 1, history["Year"].max() + horizon + 1)
        coefficients = np.polyfit(history["Year"].to_numpy(), history[metric_label].to_numpy(), deg=1)
        forecast_values = np.polyval(coefficients, future_years)
        forecast_df = pd.DataFrame(
            {
                "Year": future_years,
                metric_label: forecast_values,
                "Type": "Forecast",
            }
        )
        return pd.concat([history, forecast_df], ignore_index=True)

    def build_world_snapshot(self, df: pd.DataFrame, columns: dict[str, str]) -> dict[str, Any]:
        world_df = df[df["Region"] == WORLD_ENTITY_NAME].sort_values("Year")
        if world_df.empty:
            country_only = df[df["Entity Type"] == "Country"].copy()
            latest_year = int(country_only["Year"].max())
            previous_year = (
                int(sorted(country_only["Year"].unique())[-2])
                if country_only["Year"].nunique() > 1
                else latest_year
            )
            latest = country_only[country_only["Year"] == latest_year]
            previous = country_only[country_only["Year"] == previous_year]
            world_supply = float(latest[columns["supply"]].sum())
            previous_supply = float(previous[columns["supply"]].sum())
            avg_per_capita = float(latest[columns["percap"]].mean())
            country_df = latest
        else:
            latest = world_df.iloc[-1]
            previous = world_df.iloc[-2] if len(world_df) > 1 else latest
            latest_year = int(latest["Year"])
            world_supply = float(latest[columns["supply"]])
            previous_supply = float(previous[columns["supply"]])
            avg_per_capita = float(latest[columns["percap"]])
            country_df = df[(df["Year"] == latest_year) & (df["Entity Type"] == "Country")]

        return {
            "latest_year": latest_year,
            "world_supply": world_supply,
            "world_supply_delta_pct": self._pct_change(previous_supply, world_supply),
            "avg_per_capita": avg_per_capita,
            "importer_share_pct": float((country_df["is_importer"].mean()) * 100),
            "countries_covered": int(country_df["Region"].nunique()),
        }

    @staticmethod
    def _pct_change(previous: float, current: float) -> float:
        if previous == 0:
            return 0.0
        return ((current - previous) / abs(previous)) * 100.0
