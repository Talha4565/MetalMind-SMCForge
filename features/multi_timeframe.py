"""
Multi-timeframe feature aggregation.
Combines features from multiple timeframes (5m, 15m, 30m, 1h) for richer context.
"""

import pandas as pd
import numpy as np
from typing import Dict, List


def add_higher_timeframe_features(df: pd.DataFrame, 
                                  higher_tf_cols: List[str],
                                  suffix: str) -> pd.DataFrame:
    """
    Extract key features from higher timeframe data.
    
    Args:
        df: Primary timeframe DataFrame (already contains aligned higher TF data)
        higher_tf_cols: List of higher timeframe columns (e.g., ['1h_close', '1h_high', ...])
        suffix: Suffix to identify features (e.g., '1h')
    
    Returns:
        DataFrame with aggregated higher timeframe features
    """
    df = df.copy()
    
    # Extract higher timeframe OHLC
    close_col = f"{suffix}_close"
    high_col = f"{suffix}_high"
    low_col = f"{suffix}_low"
    
    if close_col not in df.columns:
        return df
    
    # Trend direction (EMA crossover on higher TF)
    ema_fast = df[close_col].ewm(span=20).mean()
    ema_slow = df[close_col].ewm(span=50).mean()
    df[f'htf_{suffix}_trend'] = (ema_fast > ema_slow).astype(int)
    
    # Volatility (ATR on higher TF)
    high_low = df[high_col] - df[low_col]
    high_close = abs(df[high_col] - df[close_col].shift(1))
    low_close = abs(df[low_col] - df[close_col].shift(1))
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df[f'htf_{suffix}_atr'] = true_range.rolling(14).mean() / df[close_col]
    
    # RSI on higher TF
    delta = df[close_col].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0).rolling(14).mean()
    rs = gain / loss
    df[f'htf_{suffix}_rsi'] = 100 - (100 / (1 + rs))
    
    # Distance from recent high/low (support/resistance)
    rolling_high = df[high_col].rolling(50).max()
    rolling_low = df[low_col].rolling(50).min()
    df[f'htf_{suffix}_dist_high'] = (df[close_col] - rolling_high) / df[close_col]
    df[f'htf_{suffix}_dist_low'] = (df[close_col] - rolling_low) / df[close_col]
    
    # Momentum (rate of change)
    df[f'htf_{suffix}_momentum'] = df[close_col].pct_change(10)
    
    return df


def add_all_multi_timeframe_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add features from all available higher timeframes.
    
    Assumes df already has aligned columns from data loader:
    - 5m_close, 5m_high, etc.
    - 30m_close, 30m_high, etc.
    - 1h_close, 1h_high, etc.
    
    Args:
        df: Aligned multi-timeframe DataFrame
    
    Returns:
        DataFrame with aggregated multi-timeframe features
    """
    df = df.copy()
    
    # Check which timeframes are available
    available_tfs = []
    for tf in ['5m', '30m', '1h']:
        if f'{tf}_close' in df.columns:
            available_tfs.append(tf)
    
    # Add features from each higher timeframe
    for tf in available_tfs:
        cols = [c for c in df.columns if c.startswith(f'{tf}_')]
        if cols:
            df = add_higher_timeframe_features(df, cols, tf)
    
    return df


if __name__ == "__main__":
    print("Multi-timeframe feature aggregation module loaded.")
    print("Use add_all_multi_timeframe_features() on aligned data from loaders.py")
