import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import logging

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """
    Performs automated feature engineering and transformation.
    
    Provides methods to:
    - Automatically detect energy-related columns
    - Create binary target variables (importer classification)
    - Generate derived features (log transformations)
    - Scale and normalize features
    - Document all transformations
    
    Attributes:
        df (pd.DataFrame): Working dataframe
        scaler (StandardScaler): Fitted scaler for inverse transformation
        feature_log (dict): Log of all feature engineering steps
        original_df (pd.DataFrame): Original data before transformations
    """

    def __init__(self, df):
        """
        Initialize FeatureEngineer.
        
        Args:
            df (pd.DataFrame): Input dataframe with energy data
        """
        self.df = df.copy()
        self.original_df = df.copy()
        self.scaler = None
        self.feature_log = {}

    def _detect_columns(self):
        """
        Automatically detect energy-related columns by pattern matching.
        
        This method searches for columns containing specific keywords
        to identify primary production, imports, stock changes, etc.
        Handles variations in column naming conventions.
        
        Returns:
            dict: Mapping of column types to actual column names
        """
        cols = list(self.df.columns)

        col_prod = next((c for c in cols if "Primary energy production" in c), None)
        col_netimp = next((c for c in cols if "Net imports" in c), None)
        col_stock = next((c for c in cols if "Changes in stocks" in c), None)
        col_supply = next((c for c in cols if "Total supply" in c), None)
        col_percap = next((c for c in cols if "per capita" in c), None)

        detected = {
            "prod": col_prod,
            "netimp": col_netimp,
            "stock": col_stock,
            "supply": col_supply,
            "percap": col_percap
        }
        
        logger.info(f"Detected columns: {detected}")
        return detected

    def create_features(self):
        """
        Create engineered features from raw data.
        
        Features created:
        1. is_importer: Binary variable (1 if Net imports > 0, else 0)
        2. Log transformations: Safe log(1+x) for prod, netimp, supply
        
        These features capture:
        - Binary classification of importer/exporter status
        - Non-linear relationships through log transformation
        - Reduced impact of outliers
        
        Returns:
            pd.DataFrame: Data with new engineered features
        """
        cols = self._detect_columns()

        # Feature 1: is_importer flag
        if cols["netimp"] in self.df.columns:
            self.df["is_importer"] = (self.df[cols["netimp"]] > 0).astype(int)
            self.feature_log["is_importer"] = "Binary flag: 1 if Net imports > 0, else 0"
            logger.info(f"Created is_importer feature: {self.df['is_importer'].value_counts().to_dict()}")
        else:
            logger.warning("Net imports column not found. Setting is_importer to 0")
            self.df["is_importer"] = 0

        # Feature 2: Log transformations for skewed features
        for key in ["prod", "netimp", "supply"]:
            col = cols[key]
            if col in self.df.columns:
                self.df[f"{col}_log"] = np.log1p(self.df[col].clip(lower=0))
                self.feature_log[f"{col}_log"] = f"Log transformation: log(1 + {col})"
                logger.info(f"Created log feature: {col}_log")

        logger.info(f"Feature engineering complete. Created {len(self.feature_log)} new features")
        return self.df

    def scale_numeric(self, numeric_cols):
        """
        Apply standardization (z-score normalization) to numeric features.
        
        This transformation:
        - Centers features at 0
        - Scales to unit variance
        - Improves model convergence
        - Essential for distance-based algorithms
        
        Args:
            numeric_cols (list): Column names to scale
        
        Returns:
            tuple: (scaled_df, scaler) for inverse transformation capability
            
        Note:
            Only scales columns that exist in the dataframe.
        """
        self.scaler = StandardScaler()

        # Filter to only existing columns
        numeric_cols = [c for c in numeric_cols if c in self.df.columns]

        if len(numeric_cols) == 0:
            logger.warning("No numeric columns to scale")
            return self.df, None

        self.df[numeric_cols] = self.scaler.fit_transform(self.df[numeric_cols])
        logger.info(f"Scaled {len(numeric_cols)} numeric columns: {numeric_cols}")

        return self.df, self.scaler
    
    def get_feature_report(self):
        """
        Generate a report of all feature engineering transformations.
        
        Returns:
            dict: Log of all created features and their definitions
        """
        return self.feature_log
