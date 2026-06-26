"""
Data loading pipeline for multi-timeframe analysis.
Handles all 4 timeframes (5m, 15m, 30m, 1h) and aligns them for feature engineering.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

from config.settings import ASSETS, get_asset_file, get_session_times

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MultiTimeframeLoader:
    """Loads and aligns multiple timeframes for a single asset."""
    
    def __init__(self, asset: str = "gold"):
        self.asset = asset
        self.timeframes = {}
        
    def load_timeframe(self, tf: str) -> pd.DataFrame:
        """Load a single timeframe CSV file."""
        file_path = get_asset_file(self.asset, tf)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Data file not found: {file_path}")
        
        logger.info(f"Loading {tf} data from {file_path}")
        
        df = pd.read_csv(file_path)
        
        # Handle separate Date/Time columns
        if 'Date' in df.columns and 'Time' in df.columns:
            df['DateTime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], format='mixed')
            df.drop(columns=['Date', 'Time'], inplace=True)
        elif 'Date' in df.columns:
            df['DateTime'] = pd.to_datetime(df['Date'])
            df.drop(columns=['Date'], inplace=True)
        
        df.set_index('DateTime', inplace=True)
        df.sort_index(inplace=True)
        
        # Remove duplicate timestamps (can occur in synthetic data)
        if df.index.duplicated().any():
            logger.warning(f"Found {df.index.duplicated().sum()} duplicate timestamps, removing...")
            df = df[~df.index.duplicated(keep='first')]
        
        # Rename columns to standard format
        df.rename(columns={
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        }, inplace=True)
        
        logger.info(f"Loaded {len(df)} rows from {df.index.min()} to {df.index.max()}")
        
        return df
    
    def load_all_timeframes(self, timeframes: List[str] = None) -> Dict[str, pd.DataFrame]:
        """Load all specified timeframes."""
        if timeframes is None:
            timeframes = ["5m", "15m", "30m", "1h"]
        
        self.timeframes = {}
        for tf in timeframes:
            try:
                self.timeframes[tf] = self.load_timeframe(tf)
            except Exception as e:
                logger.warning(f"Could not load {tf}: {e}")
        
        return self.timeframes
    
    def align_to_primary(self, primary_tf: str = "15m") -> pd.DataFrame:
        """
        Align all timeframes to the primary timeframe's timestamps.
        Skips any timeframe whose date range doesn't overlap significantly
        with the primary (prevents short-lived feeds from NaN-ifying the dataset).
        """
        if primary_tf not in self.timeframes:
            raise ValueError(f"Primary timeframe {primary_tf} not loaded")

        primary = self.timeframes[primary_tf].copy()
        primary_start = primary.index.min()
        primary_end = primary.index.max()
        primary_span = (primary_end - primary_start).days

        logger.info(f"Aligning all timeframes to {primary_tf} (primary)")

        for tf, df in self.timeframes.items():
            if tf == primary_tf:
                continue

            # Skip timeframes that cover less than 50% of the primary range
            tf_span = (df.index.max() - df.index.min()).days
            if tf_span < primary_span * 0.5:
                logger.info(f"  Skipping {tf}: only {tf_span} days vs {primary_span} days primary")
                continue

            aligned = df.reindex(primary.index, method='ffill')
            aligned.columns = [f"{tf}_{col}" for col in aligned.columns]
            primary = primary.join(aligned, how='left')

        logger.info(f"Aligned dataset shape: {primary.shape}")
        return primary
    
    def apply_session_filter(self, df: pd.DataFrame, 
                            start_time: str = None, 
                            end_time: str = None) -> pd.DataFrame:
        """Filter to specific trading session (e.g., London+NY overlap)."""
        session_config = get_session_times()
        
        if not session_config['enabled']:
            return df
        
        start = start_time or session_config['start_time']
        end = end_time or session_config['end_time']
        
        logger.info(f"Applying session filter: {start} - {end}")
        filtered = df.between_time(start, end)
        logger.info(f"Filtered from {len(df)} to {len(filtered)} rows ({len(filtered)/len(df)*100:.1f}%)")
        
        return filtered
    
    def get_aligned_dataset(self, 
                           primary_tf: str = "15m",
                           apply_session: bool = True) -> pd.DataFrame:
        """
        Main method: Load all timeframes, align them, and optionally apply session filter.
        
        Returns:
            DataFrame with primary timeframe index and features from all timeframes.
        """
        # Load all timeframes
        self.load_all_timeframes()
        
        # Align to primary
        aligned = self.align_to_primary(primary_tf)
        
        # Apply session filter if requested
        if apply_session:
            aligned = self.apply_session_filter(aligned)
        
        # Drop any rows with NaN (from alignment)
        aligned.dropna(inplace=True)
        
        return aligned


def load_gold_data(primary_tf: str = "15m", 
                   session_filter: bool = True) -> pd.DataFrame:
    """
    Convenience function to load Gold data with multi-timeframe features.
    
    Args:
        primary_tf: Primary timeframe for predictions (default "15m")
        session_filter: Whether to filter to London+NY session (default True)
    
    Returns:
        DataFrame with aligned multi-timeframe data
    """
    loader = MultiTimeframeLoader(asset="gold")
    return loader.get_aligned_dataset(primary_tf, apply_session=session_filter)


def load_silver_data(primary_tf: str = "15m", 
                     session_filter: bool = True) -> pd.DataFrame:
    """
    Convenience function to load Silver data with multi-timeframe features.
    
    Args:
        primary_tf: Primary timeframe for predictions (default "15m")
        session_filter: Whether to filter to London+NY session (default True)
    
    Returns:
        DataFrame with aligned multi-timeframe data
    """
    loader = MultiTimeframeLoader(asset="silver")
    return loader.get_aligned_dataset(primary_tf, apply_session=session_filter)


def load_asset_data(asset: str = "gold",
                    primary_tf: str = "15m", 
                    session_filter: bool = True) -> pd.DataFrame:
    """
    Generic function to load any asset data with multi-timeframe features.
    
    Args:
        asset: Asset name ("gold" or "silver")
        primary_tf: Primary timeframe for predictions (default "15m")
        session_filter: Whether to filter to London+NY session (default True)
    
    Returns:
        DataFrame with aligned multi-timeframe data
    """
    loader = MultiTimeframeLoader(asset=asset)
    return loader.get_aligned_dataset(primary_tf, apply_session=session_filter)


def train_val_test_split(df: pd.DataFrame, 
                         train_pct: float = 0.70,
                         val_pct: float = 0.15,
                         test_pct: float = 0.15) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Chronological split of data into train/val/test sets.
    Maintains temporal order (no shuffling).
    
    Args:
        df: Input dataframe
        train_pct: Fraction for training (default 0.70)
        val_pct: Fraction for validation (default 0.15)
        test_pct: Fraction for testing (default 0.15)
    
    Returns:
        Tuple of (train_df, val_df, test_df)
    """
    n = len(df)
    
    if n == 0:
        raise ValueError("Cannot split empty dataframe. Check data loading and feature engineering pipeline.")
    
    train_end = int(n * train_pct)
    val_end = int(n * (train_pct + val_pct))
    
    train = df.iloc[:train_end]
    val = df.iloc[train_end:val_end]
    test = df.iloc[val_end:]
    
    logger.info(f"Split: Train={len(train)} ({len(train)/n*100:.1f}%), "
                f"Val={len(val)} ({len(val)/n*100:.1f}%), "
                f"Test={len(test)} ({len(test)/n*100:.1f}%)")
    
    return train, val, test


if __name__ == "__main__":
    # Test the loader
    print("Testing MultiTimeframeLoader...")
    
    # Load and align all timeframes
    df = load_gold_data(primary_tf="15m", session_filter=True)
    
    print(f"\nFinal dataset shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    print(f"\nFirst few rows:")
    print(df.head())
    
    # Test split
    train, val, test = train_val_test_split(df)
    print(f"\nTrain: {train.index.min()} to {train.index.max()}")
    print(f"Val: {val.index.min()} to {val.index.max()}")
    print(f"Test: {test.index.min()} to {test.index.max()}")
