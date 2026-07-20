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
        volume_sum = df['volume'].rolling(w).sum()
        # Avoid division by zero - replace zero volume with NaN, will be forward filled
        volume_sum = volume_sum.replace(0, np.nan)
        vwap = (df['close'] * df['volume']).rolling(w).sum() / volume_sum
        # Avoid division by zero in deviation calculation
        vwap = vwap.replace(0, np.nan)
        df[f'VWAPd_{w}'] = (df['close'] - vwap) / vwap
        # Fill NaN values with 0 (no deviation when volume is zero)
        df[f'VWAPd_{w}'].fillna(0, inplace=True)
    
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
        
        # Avoid division by zero - set to 0 when total volume is 0
        df[f'Imbal_{w}'] = np.where(
            total_volume > 0,
            (buy_sum - sell_sum) / total_volume,
            0  # No imbalance when volume is zero
        )
    
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
    
    # Add missing features expected by the trained model
    df = add_model_required_features(df)
    
    return df


def add_model_required_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add features required by the trained XGBoost model.
    These include CVD variants, ADX, ATR, and trend features.
    
    Args:
        df: DataFrame with OHLC columns
    
    Returns:
        DataFrame with additional features added
    """
    df = df.copy()
    
    # === CVD Variants for specific timeframes ===
    # cvd_15m: CVD using 15m data (1 bar = 15min for 15m timeframe)
    # Since we're on 15m data, 1 bar = 15m, so use rolling(1) for "current" CVD
    signed_volume = np.where(df['close'] > df['open'], df['volume'], -df['volume'])
    
    # cvd_15m: Use window=4 (1 hour = 4 x 15min bars)
    df['cvd_15m'] = pd.Series(signed_volume, index=df.index).rolling(4).sum()
    df['cvd_15m_slope'] = df['cvd_15m'].diff(4)  # Slope over 1 hour
    
    # cvd_30m: Use window=8 (2 hours = 8 x 15min bars)
    df['cvd_30m'] = pd.Series(signed_volume, index=df.index).rolling(8).sum()
    df['cvd_30m_slope'] = df['cvd_30m'].diff(8)  # Slope over 2 hours
    
    # === ADX (Average Directional Index) ===
    # ADX measures trend strength (0-100)
    period = 14
    high = df['high']
    low = df['low']
    close = df['close']
    
    # True Range
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # Directional Movement
    up_move = high - high.shift(1)
    down_move = low.shift(1) - low
    
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
    
    # Smoothed averages
    atr_smooth = pd.Series(tr, index=df.index).rolling(period).mean()
    plus_di = 100 * pd.Series(plus_dm, index=df.index).rolling(period).mean() / atr_smooth
    minus_di = 100 * pd.Series(minus_dm, index=df.index).rolling(period).mean() / atr_smooth
    
    # ADX
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    df['adx_14'] = dx.rolling(period).mean()
    df['adx_trending'] = (df['adx_14'] > 25).astype(int)  # 1 if trending
    
    # === ATR (Average True Range) ===
    df['atr_14'] = tr.rolling(period).mean()
    
    # === Trend Features ===
    # EMA 20 and EMA 50
    ema_20 = close.ewm(span=20, adjust=False).mean()
    ema_50 = close.ewm(span=50, adjust=False).mean()
    
    # trend_ema_cross: 1 if EMA20 > EMA50 (bullish), 0 otherwise
    df['trend_ema_cross'] = (ema_20 > ema_50).astype(int)
    
    # trend_price_vs_ema: Distance from price to EMA20 (normalized)
    df['trend_price_vs_ema'] = (close - ema_20) / ema_20
    
    # trend_adx: ADX value (same as adx_14 but named for model compatibility)
    df['trend_adx'] = df['adx_14']
    
    # trend_strength: Combined trend strength metric
    # Positive = bullish, Negative = bearish, magnitude = strength
    df['trend_strength'] = df['trend_ema_cross'] * 2 - 1  # +1 or -1
    df['trend_strength'] = df['trend_strength'] * (df['adx_14'] / 100)  # Scale by ADX
    
    # Fill NaN values with 0
    df['cvd_15m'].fillna(0, inplace=True)
    df['cvd_15m_slope'].fillna(0, inplace=True)
    df['cvd_30m'].fillna(0, inplace=True)
    df['cvd_30m_slope'].fillna(0, inplace=True)
    df['adx_14'].fillna(0, inplace=True)
    df['adx_trending'].fillna(0, inplace=True)
    df['atr_14'].fillna(0, inplace=True)
    df['trend_ema_cross'].fillna(0, inplace=True)
    df['trend_price_vs_ema'].fillna(0, inplace=True)
    df['trend_adx'].fillna(0, inplace=True)
    df['trend_strength'].fillna(0, inplace=True)
    
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
