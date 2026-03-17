from __future__ import annotations

from dataclasses import dataclass, field
import logging

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


@dataclass
class FeatureEngineer:
    """Create derived features and keep a lightweight transformation audit trail."""

    df: pd.DataFrame
    scaler: StandardScaler | None = field(default=None, init=False)
    feature_log: dict[str, str] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        self.df = self.df.copy()
        self.original_df = self.df.copy()

    def _detect_columns(self) -> dict[str, str | None]:
        """Detect the canonical energy columns used by the project."""
        cols = list(self.df.columns)
        detected = {
            "prod": next((c for c in cols if "Primary energy production" in c), None),
            "netimp": next((c for c in cols if "Net imports" in c), None),
            "stock": next((c for c in cols if "Changes in stocks" in c), None),
            "supply": next((c for c in cols if "Total supply" in c), None),
            "percap": next((c for c in cols if "per capita" in c.lower()), None),
        }
        logger.info("Detected project columns: %s", detected)
        return detected

    def create_features(self) -> pd.DataFrame:
        """Add reusable derived features for downstream modeling."""
        cols = self._detect_columns()

        net_imports_column = cols["netimp"]
        if net_imports_column and net_imports_column in self.df.columns:
            self.df["is_importer"] = (self.df[net_imports_column] > 0).astype(int)
            self.feature_log["is_importer"] = "Binary flag set to 1 when net imports are positive."
        else:
            self.df["is_importer"] = 0
            self.feature_log["is_importer"] = "Fallback value because no net imports column was found."

        for key in ["prod", "netimp", "stock", "supply"]:
            column = cols.get(key)
            if column and column in self.df.columns:
                engineered_name = f"{column}_log1p"
                # Clip negatives to zero so the transform stays valid for trade balance columns.
                self.df[engineered_name] = np.log1p(self.df[column].clip(lower=0))
                self.feature_log[engineered_name] = f"Log1p transform derived from `{column}`."

        logger.info("Created %s engineered features", len(self.feature_log))
        return self.df.copy()

    def scale_numeric(self, numeric_cols: list[str]) -> tuple[pd.DataFrame, StandardScaler | None]:
        """Standardize selected columns and return the transformed dataframe."""
        existing_columns = [column for column in numeric_cols if column in self.df.columns]
        if not existing_columns:
            logger.warning("No matching numeric columns were provided for scaling")
            return self.df.copy(), None

        self.scaler = StandardScaler()
        self.df.loc[:, existing_columns] = self.scaler.fit_transform(self.df[existing_columns])
        self.feature_log["scaled_columns"] = ", ".join(existing_columns)
        logger.info("Scaled %s numeric columns", len(existing_columns))
        return self.df.copy(), self.scaler

    def get_feature_report(self) -> dict[str, str]:
        """Return a simple record of feature engineering steps."""
        return dict(self.feature_log)
