"""Clean and validate data quality."""

import pandas as pd
import numpy as np
from .base import BaseTransformer
from ..exceptions import TransformationError
import logging

logger = logging.getLogger(__name__)


class DataQualityTransformer(BaseTransformer):
    """Clean and validate data quality."""
    
    def __init__(
        self,
        handle_missing: str = 'ffill',
        remove_duplicates: bool = True,
        remove_outliers: bool = True,
        outlier_std: float = 5.0,
        **kwargs
    ):
        super().__init__(kwargs)
        self.handle_missing = handle_missing
        self.remove_duplicates = remove_duplicates
        self.remove_outliers = remove_outliers
        self.outlier_std = outlier_std
    
    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """Apply data quality transformations."""
        if data.empty:
            raise TransformationError("Cannot transform empty DataFrame")
        
        df = data.copy()
        initial_rows = len(df)
        
        # Remove duplicates
        if self.remove_duplicates:
            if 'timestamp' in df.columns:
                df = df.drop_duplicates(subset=['timestamp'], keep='first')
                removed = initial_rows - len(df)
                if removed > 0:
                    logger.info(f"Removed {removed} duplicate rows")
        
        # Handle missing values
        if self.handle_missing == 'ffill':
            df = df.ffill()  # Updated method
            logger.info("Applied forward fill for missing values")
        elif self.handle_missing == 'bfill':
            df = df.bfill()  # Updated method
            logger.info("Applied backward fill for missing values")
        elif self.handle_missing == 'drop':
            before = len(df)
            df = df.dropna()
            dropped = before - len(df)
            if dropped > 0:
                logger.info(f"Dropped {dropped} rows with missing values")
        
        # Remove outliers
        if self.remove_outliers:
            df = self._remove_outliers(df)
        
        # Validate OHLC consistency
        df = self._validate_ohlc(df)
        
        final_rows = len(df)
        logger.info(f"Data quality: {initial_rows} -> {final_rows} rows ({final_rows/initial_rows*100:.1f}% retained)")
        
        return df
    
    def _remove_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove statistical outliers."""
        initial_len = len(df)
        
        for col in ['open', 'high', 'low', 'close']:
            if col in df.columns:
                mean = df[col].mean()
                std = df[col].std()
                
                if std == 0:
                    continue
                
                mask = np.abs(df[col] - mean) <= self.outlier_std * std
                outliers = (~mask).sum()
                
                if outliers > 0:
                    logger.warning(f"Found {outliers} outliers in '{col}' column")
                    df = df[mask]
        
        removed = initial_len - len(df)
        if removed > 0:
            logger.info(f"Removed {removed} outlier rows")
        
        return df
    
    def _validate_ohlc(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate OHLC price consistency."""
        if not all(col in df.columns for col in ['open', 'high', 'low', 'close']):
            return df
        
        # High should be >= Open, Close, and Low
        invalid_high = df['high'] < df[['open', 'close', 'low']].max(axis=1)
        
        # Low should be <= Open, Close, and High
        invalid_low = df['low'] > df[['open', 'close', 'high']].min(axis=1)
        
        invalid_mask = invalid_high | invalid_low
        invalid_count = invalid_mask.sum()
        
        if invalid_count > 0:
            logger.warning(f"Found {invalid_count} rows with invalid OHLC relationships")
            df = df[~invalid_mask]
        
        return df
