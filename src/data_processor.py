from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import logging

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class DataProcessor:
    """Load and reshape the UN energy dataset into analysis-ready tabular data."""

    filepath: str | Path
    df: pd.DataFrame | None = field(default=None, init=False)
    original_df: pd.DataFrame | None = field(default=None, init=False)
    missing_value_stats: dict[str, Any] = field(default_factory=dict, init=False)

    def load_data(self) -> pd.DataFrame:
        """Load the raw CSV and normalize the header layout used by the source file."""
        path = Path(self.filepath)
        if not path.exists():
            raise FileNotFoundError(f"Dataset not found: {path}")

        raw = pd.read_csv(path)
        if raw.empty:
            raise ValueError(f"Dataset is empty: {path}")

        header = raw.iloc[0].tolist()
        df = raw.iloc[1:].copy()
        df.columns = header

        required_columns = ["Region/Country/Area", "Year", "Series", "Value"]
        missing_columns = [column for column in required_columns if column not in df.columns]
        if missing_columns:
            raise ValueError(
                "Dataset header is missing required columns: "
                + ", ".join(sorted(missing_columns))
            )

        renamed = df.rename(
            columns={
                "Region/Country/Area": "RegionCode",
                header[1]: "Region",
                "Year": "Year",
                "Series": "Series",
                "Value": "Value",
            }
        )

        self.original_df = renamed[["RegionCode", "Region", "Year", "Series", "Value"]].copy()
        self.df = self.original_df.copy()

        logger.info("Loaded %s records from %s", len(self.df), path)
        return self.df.copy()

    def clean(self) -> pd.DataFrame:
        """Convert types, drop incomplete rows, and pivot to a wide modeling table."""
        if self.df is None:
            raise ValueError("Data not loaded. Call load_data() first.")

        df = self.df.copy()
        initial_rows = len(df)
        initial_missing = int(df.isna().sum().sum())

        df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
        df["Value"] = pd.to_numeric(
            df["Value"].astype(str).str.replace(",", "", regex=False),
            errors="coerce",
        )
        df["Region"] = df["Region"].astype(str).str.strip()
        df["Series"] = df["Series"].astype(str).str.strip()

        df = df.dropna(subset=["Year", "Value", "Series", "Region"])
        df = df[df["Region"].ne("")]
        df["Year"] = df["Year"].astype(int)

        df_wide = (
            df.pivot_table(
                index=["Region", "Year"],
                columns="Series",
                values="Value",
                aggfunc="first",
            )
            .reset_index()
            .sort_values(["Region", "Year"])
            .reset_index(drop=True)
        )
        df_wide.columns.name = None

        self.missing_value_stats = {
            "initial_rows": initial_rows,
            "rows_removed": initial_rows - len(df),
            "initial_missing_values": initial_missing,
            "final_shape": df_wide.shape,
        }
        self.df = df_wide

        logger.info("Prepared wide dataset with shape %s", df_wide.shape)
        return df_wide.copy()

    def get_processed_data(self) -> pd.DataFrame | None:
        """Return the latest in-memory dataframe."""
        return None if self.df is None else self.df.copy()

    def get_summary_stats(self) -> dict[str, Any]:
        """Return metadata collected during cleaning."""
        return dict(self.missing_value_stats)
