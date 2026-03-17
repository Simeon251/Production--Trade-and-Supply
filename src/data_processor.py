import pandas as pd
import numpy as np
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataProcessor:
    """
    Handles data loading, cleaning, and transformation for the UN energy dataset.
    
    This class provides methods to:
    - Load and parse CSV data with custom headers
    - Perform data type conversions and cleaning
    - Handle missing values and outliers
    - Transform data from long to wide format
    
    Attributes:
        filepath (str): Path to the CSV file
        df (pd.DataFrame): Current working dataframe
        original_df (pd.DataFrame): Original loaded data for reference
        missing_value_stats (dict): Statistics about missing values during cleaning
    """

    def __init__(self, filepath):
        """
        Initialize DataProcessor.
        
        Args:
            filepath (str): Path to the UN energy CSV file
        """
        self.filepath = filepath
        self.df = None
        self.original_df = None
        self.missing_value_stats = {}

    def load_data(self):
        """
        Load CSV data and handle custom header structure.
        
        The first row contains the actual column names.
        Renames and selects essential columns for analysis.
        
        Returns:
            pd.DataFrame: Loaded data with renamed columns
            
        Raises:
            FileNotFoundError: If filepath does not exist
            pd.errors.ParserError: If CSV is malformed
        """
        try:
            raw = pd.read_csv(self.filepath)
            logger.info(f"Loaded {len(raw)} rows from {self.filepath}")
        except FileNotFoundError:
            logger.error(f"File not found: {self.filepath}")
            raise
        except pd.errors.ParserError as e:
            logger.error(f"Error parsing CSV: {e}")
            raise

        # First row contains the TRUE header
        header = raw.iloc[0].tolist()
        df = raw.iloc[1:].copy()
        df.columns = header

        # Standardize column names
        df = df.rename(columns={
            "Region/Country/Area": "RegionCode",
            header[1]: "Region",
            "Year": "Year",
            "Series": "Series",
            "Value": "Value"
        })

        df = df[["RegionCode", "Region", "Year", "Series", "Value"]]
        self.original_df = df.copy()
        self.df = df.copy()
        
        logger.info(f"Data loaded successfully with {len(df)} records")
        return df

    def clean(self):
        """
        Clean data by converting types, handling missing values, and pivoting.
        
        Steps:
        1. Convert Year and Value to numeric types
        2. Remove rows with missing critical values
        3. Pivot from long to wide format
        
        Returns:
            pd.DataFrame: Cleaned data in wide format
        """
        if self.df is None:
            logger.error("No data to clean. Call load_data() first.")
            raise ValueError("Data not loaded. Call load_data() first.")
            
        df = self.df.copy()
        
        # Record initial missing values
        initial_missing = df.isnull().sum().sum()
        
        # Convert Year and Value to numeric
        df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
        df["Value"] = df["Value"].astype(str).str.replace(",", "", regex=False)
        df["Value"] = pd.to_numeric(df["Value"], errors="coerce")

        # Remove rows with missing critical values
        df = df.dropna(subset=["Year", "Value", "Series", "Region"])
        
        rows_removed = len(self.df) - len(df)
        logger.info(f"Removed {rows_removed} rows with missing values")
        self.missing_value_stats["rows_removed"] = rows_removed
        self.missing_value_stats["initial_missing"] = initial_missing

        # Pivot long → wide format
        df_wide = df.pivot_table(
            index=["Region", "Year"],
            columns="Series",
            values="Value",
            aggfunc="first"
        ).reset_index()

        df_wide.columns.name = None
        self.df = df_wide
        
        logger.info(f"Pivoted data to wide format: {df_wide.shape[0]} rows, {df_wide.shape[1]} columns")
        return df_wide

    def get_processed_data(self):
        """
        Retrieve the current working dataframe.
        
        Returns:
            pd.DataFrame: Processed data
        """
        return self.df
    
    def get_summary_stats(self):
        """
        Return summary statistics about the data cleaning process.
        
        Returns:
            dict: Statistics including rows removed and missing value counts
        """
        return self.missing_value_stats
