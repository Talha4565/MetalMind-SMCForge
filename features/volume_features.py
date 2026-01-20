"""
Volume-based microstructure features.
These are the proven features from your existing 73% accuracy model.
"""

import pandas as pd
import numpy as np
from typing import List


def add_vwap_deviation(df: pd.DataFrame, windows: List[int] = [4, 16, 96]) -> pd.DataFrame:
    """
    Volume-Weighted Average Price deviation.
    Measures how far current price is from VWAP.
    
    Args:
        df: DataFrame with 'close' and 'volume' columns
        windows: List of rolling windows (in bars)
    
    Returns:
        DataFrame with added VWAPd_N columns
    """
    df = df.copy()
    
    for w in windows:
        vwap = (df['close'] * df['volume']).rolling(w).sum() / df['volume'].rolling(w).sum()
        df[f'VWAPd_{w}'] = (df['close'] - vwap) / vwap
    
    return df


def add_cumulative_volume_delta(df: pd.DataFrame, windows: List[int] = [4, 16, 96]) -> pd.DataFrame:
    """
    Cumulative Volume Delta (CVD).
    Measures buying vs selling pressure based on candle direction.
    
    Green candle (close > open) → positive volume
    Red candle (close < open) → negative volume
    
    Args:
        df: DataFrame with 'open', 'close', 'volume' columns
        windows: List of rolling windows
    
    Returns:
        DataFrame with added CVD_N columns
    """
    df = df.copy()
    
    # Signed volume (positive if bullish, negative if bearish)
    signed_volume = np.where(df['close'] > df['open'], df['volume'], -df['volume'])
    
    for w in windows:
        df[f'CVD_{w}'] = pd.Series(signed_volume, index=df.index).rolling(w).sum()
    
    return df


def add_volume_imbalance(df: pd.DataFrame, windows: List[int] = [4, 16, 96]) -> pd.DataFrame:
    """
    Volume Imbalance.
    Ratio of buying volume to selling volume.
    
    Args:
        df: DataFrame with 'open', 'close', 'volume' columns
        windows: List of rolling windows
    
    Returns:
        DataFrame with added Imbal_N columns
    """
    df = df.copy()
    
    # Buy volume (green candles only)
    buy_volume = pd.Series(
        np.where(df['close'] > df['open'], df['volume'], 0),
        index=df.index
    )
    
    # Sell volume (red candles only)
    sell_volume = pd.Series(
        np.where(df['close'] < df['open'], df['volume'], 0),
        index=df.index
    )
    
    for w in windows:
        buy_sum = buy_volume.rolling(w).sum()
        sell_sum = sell_volume.rolling(w).sum()
        total_volume = df['volume'].rolling(w).sum()
        
        df[f'Imbal_{w}'] = (buy_sum - sell_sum) / total_volume
    
    return df


def add_wick_ratio(df: pd.DataFrame, windows: List[int] = [4, 16, 96]) -> pd.DataFrame:
    """
    Wick Ratio.
    Measures rejection strength (large wicks = rejection of price level).
    
    Args:
        df: DataFrame with OHLC columns
        windows: List of rolling windows
    
    Returns:
        DataFrame with added Wick_N columns
    """
    df = df.copy()
    
    # Upper wick: high - max(open, close)
    # Lower wick: min(open, close) - low
    # Total wick: max of both
    wick_size = np.maximum(
        df['high'] - df[['open', 'close']].max(axis=1),
        df[['open', 'close']].min(axis=1) - df['low']
    )
    
    candle_range = df['high'] - df['low']
    
    for w in windows:
        avg_wick = wick_size.rolling(w).mean()
        avg_range = candle_range.rolling(w).mean()
        
        df[f'Wick_{w}'] = avg_wick / avg_range
    
    return df


def add_basic_returns_volatility(df: pd.DataFrame, windows: List[int] = [4, 16, 96]) -> pd.DataFrame:
    """
    Basic price returns and volatility.
    
    Args:
        df: DataFrame with 'close' column
        windows: List of rolling windows
    
    Returns:
        DataFrame with added Ret_N and Std_N columns
    """
    df = df.copy()
    
    for w in windows:
        df[f'Ret_{w}'] = df['close'].pct_change(w)
        df[f'Std_{w}'] = df['close'].pct_change().rolling(w).std()
    
    return df


def add_session_flags(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add trading session binary flags.
    
    Sessions (UTC):
    - Asia: 00:00 - 08:00
    - London: 08:00 - 16:00
    - New York: 13:00 - 21:00 (overlaps with London)
    
    Args:
        df: DataFrame with datetime index
    
    Returns:
        DataFrame with added session flag columns
    """
    df = df.copy()
    
    hour = df.index.hour
    
    df['session_asia'] = (hour < 8).astype(int)
    df['session_london'] = ((hour >= 8) & (hour < 16)).astype(int)
    df['session_ny'] = (hour >= 13).astype(int)
    df['session_overlap'] = ((hour >= 13) & (hour < 16)).astype(int)  # London+NY overlap
    
    return df


def add_all_volume_features(df: pd.DataFrame, windows: List[int] = [4, 16, 96]) -> pd.DataFrame:
    """
    Add all volume-based microstructure features.
    This is the complete set from your existing 73% accuracy model.
    
    Args:
        df: DataFrame with OHLC columns
        windows: List of rolling windows (default: 1h, 4h, 24h on 15m)
    
    Returns:
        DataFrame with all volume features added
    """
    df = df.copy()
    
    # Volume microstructure
    df = add_vwap_deviation(df, windows)
    df = add_cumulative_volume_delta(df, windows)
    df = add_volume_imbalance(df, windows)
    df = add_wick_ratio(df, windows)
    
    # Price dynamics
    df = add_basic_returns_volatility(df, windows)
    
    # Session flags
    df = add_session_flags(df)
    
    return df


if __name__ == "__main__":
    # Test the features
    print("Testing volume features...")
    
    # Create sample data
    dates = pd.date_range('2024-01-01', periods=1000, freq='15min')
    df = pd.DataFrame({
        'open': np.random.randn(1000).cumsum() + 1800,
        'high': np.random.randn(1000).cumsum() + 1805,
        'low': np.random.randn(1000).cumsum() + 1795,
        'close': np.random.randn(1000).cumsum() + 1800,
        'volume': np.random.randint(100, 1000, 1000)
    }, index=dates)
    
    # Add features
    df = add_all_volume_features(df)
    
    print(f"\nOriginal columns: ['open', 'high', 'low', 'close', 'volume']")
    print(f"After features: {len(df.columns)} columns")
    print(f"\nNew feature columns:")
    new_cols = [c for c in df.columns if c not in ['open', 'high', 'low', 'close', 'volume']]
    print(new_cols)
    print(f"\nSample data:")
    print(df[new_cols].head())
