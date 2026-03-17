from __future__ import annotations

from dataclasses import dataclass, field
from io import StringIO
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import urlopen
import logging
import os

import pandas as pd

logger = logging.getLogger(__name__)

DEFAULT_DATA_URLS = [
    "https://data.un.org/_Docs/SYB/CSV/SYB68_263_202511_Production%2C%20Trade%20and%20Supply%20of%20Energy.csv",
    "https://data.un.org/_Docs/SYB/CSV/SYB67_263_202411_Production%2C%20Trade%20and%20Supply%20of%20Energy.csv",
]


@dataclass
class DataProcessor:
    """Fetch and reshape the UN energy dataset into analysis-ready tabular data."""

    source_url: str | None = None
    timeout_seconds: int = 60
    df: pd.DataFrame | None = field(default=None, init=False)
    original_df: pd.DataFrame | None = field(default=None, init=False)
    missing_value_stats: dict[str, Any] = field(default_factory=dict, init=False)
    resolved_source_url: str | None = field(default=None, init=False)

    def _candidate_urls(self) -> list[str]:
        """Return the remote URLs to try, preferring explicit or environment overrides."""
        if self.source_url:
            return [self.source_url]

        env_url = os.getenv("UN_ENERGY_DATA_URL")
        if env_url:
            return [env_url]

        return list(DEFAULT_DATA_URLS)

    def _download_csv(self) -> pd.DataFrame:
        """Download the raw CSV from the first working official UN endpoint."""
        last_error: Exception | None = None

        for url in self._candidate_urls():
            try:
                with urlopen(url, timeout=self.timeout_seconds) as response:
                    raw_bytes = response.read()
                try:
                    payload = raw_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    payload = raw_bytes.decode("latin-1")
                self.resolved_source_url = url
                logger.info("Downloaded dataset from %s", url)
                return pd.read_csv(StringIO(payload))
            except (HTTPError, URLError, TimeoutError, UnicodeDecodeError) as exc:
                last_error = exc
                logger.warning("Failed to download dataset from %s: %s", url, exc)

        raise RuntimeError("Unable to download the UN energy dataset from the configured URLs") from last_error

    def load_data(self) -> pd.DataFrame:
        """Load the raw CSV and normalize the source header layout."""
        raw = self._download_csv()
        if raw.empty:
            raise ValueError("Downloaded dataset is empty")

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
        logger.info("Loaded %s records from remote source", len(self.df))
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
            "source_url": self.resolved_source_url,
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
