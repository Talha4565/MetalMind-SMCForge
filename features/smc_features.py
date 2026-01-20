"""
Smart Money Concepts (SMC) feature engineering.
Implements institutional trading patterns used by professional traders.

Key concepts:
- Fair Value Gaps (FVG): Inefficient price zones that may get filled
- Break of Structure (BOS): Key trend changes
- Liquidity Sweeps: Stop hunts before reversals
- Order Blocks: Institutional supply/demand zones
- Premium/Discount: Price relative to recent range
"""

import pandas as pd
import numpy as np
from typing import Tuple, Optional


def detect_fair_value_gaps(df: pd.DataFrame, threshold: float = 0.0005) -> pd.DataFrame:
    """
    Fair Value Gap (FVG) detection.
    
    A bullish FVG occurs when:
    - Candle 1 high < Candle 3 low (gap in price)
    - Gap size > threshold
    
    A bearish FVG occurs when:
    - Candle 1 low > Candle 3 high
    
    Args:
        df: DataFrame with OHLC data
        threshold: Minimum gap size as fraction of price (default 0.05%)
    
    Returns:
        DataFrame with FVG columns added
    """
    df = df.copy()
    
    # Look at 3-candle patterns
    high_lag2 = df['high'].shift(2)
    low_lag2 = df['low'].shift(2)
    
    # Bullish FVG: gap up (previous high < current low)
    bullish_gap = df['low'] - high_lag2
    bullish_fvg = (bullish_gap > 0) & (bullish_gap / df['close'] > threshold)
    
    # Bearish FVG: gap down (previous low > current high)
    bearish_gap = low_lag2 - df['high']
    bearish_fvg = (bearish_gap > 0) & (bearish_gap / df['close'] > threshold)
    
    df['fvg_bullish'] = bullish_fvg.astype(int)
    df['fvg_bearish'] = bearish_fvg.astype(int)
    df['fvg_size'] = np.where(bullish_fvg, bullish_gap / df['close'],
                               np.where(bearish_fvg, bearish_gap / df['close'], 0))
    
    # Rolling count of recent FVGs (last 20 bars)
    df['fvg_bullish_count'] = df['fvg_bullish'].rolling(20).sum()
    df['fvg_bearish_count'] = df['fvg_bearish'].rolling(20).sum()
    
    return df


def detect_break_of_structure(df: pd.DataFrame, lookback: int = 20) -> pd.DataFrame:
    """
    Break of Structure (BOS) detection.
    
    Bullish BOS: Price breaks above recent swing high
    Bearish BOS: Price breaks below recent swing low
    
    Args:
        df: DataFrame with OHLC data
        lookback: Number of bars to look back for swing highs/lows
    
    Returns:
        DataFrame with BOS columns added
    """
    df = df.copy()
    
    # Recent swing high/low (rolling max/min)
    swing_high = df['high'].rolling(lookback).max()
    swing_low = df['low'].rolling(lookback).min()
    
    # BOS occurs when price crosses these levels
    bullish_bos = (df['close'] > swing_high.shift(1)) & (df['close'].shift(1) <= swing_high.shift(2))
    bearish_bos = (df['close'] < swing_low.shift(1)) & (df['close'].shift(1) >= swing_low.shift(2))
    
    df['bos_bullish'] = bullish_bos.astype(int)
    df['bos_bearish'] = bearish_bos.astype(int)
    
    # Distance from structure (normalized)
    df['distance_from_swing_high'] = (df['close'] - swing_high) / df['close']
    df['distance_from_swing_low'] = (df['close'] - swing_low) / df['close']
    
    # Rolling count of recent BOS
    df['bos_bullish_count'] = df['bos_bullish'].rolling(20).sum()
    df['bos_bearish_count'] = df['bos_bearish'].rolling(20).sum()
    
    return df


def detect_liquidity_sweeps(df: pd.DataFrame, lookback: int = 10, sweep_threshold: float = 0.0002) -> pd.DataFrame:
    """
    Liquidity Sweep detection.
    
    A liquidity sweep occurs when:
    1. Price briefly breaks a recent high/low (triggering stops)
    2. Then reverses quickly (institutional entry)
    
    Args:
        df: DataFrame with OHLC data
        lookback: Bars to look back for highs/lows
        sweep_threshold: Minimum sweep size as fraction of price
    
    Returns:
        DataFrame with liquidity sweep columns added
    """
    df = df.copy()
    
    # Recent highs/lows
    recent_high = df['high'].rolling(lookback).max().shift(1)
    recent_low = df['low'].rolling(lookback).min().shift(1)
    
    # Sweep high: wick above recent high, then close below
    sweep_high = (df['high'] > recent_high) & (df['close'] < recent_high)
    sweep_size_high = (df['high'] - recent_high) / df['close']
    valid_sweep_high = sweep_high & (sweep_size_high > sweep_threshold)
    
    # Sweep low: wick below recent low, then close above
    sweep_low = (df['low'] < recent_low) & (df['close'] > recent_low)
    sweep_size_low = (recent_low - df['low']) / df['close']
    valid_sweep_low = sweep_low & (sweep_size_low > sweep_threshold)
    
    df['liquidity_sweep_high'] = valid_sweep_high.astype(int)
    df['liquidity_sweep_low'] = valid_sweep_low.astype(int)
    df['sweep_strength'] = np.where(valid_sweep_high, sweep_size_high,
                                     np.where(valid_sweep_low, sweep_size_low, 0))
    
    # Rolling count
    df['liquidity_sweep_count'] = (df['liquidity_sweep_high'] + df['liquidity_sweep_low']).rolling(20).sum()
    
    return df


def detect_order_blocks(df: pd.DataFrame, strength_threshold: float = 0.0015) -> pd.DataFrame:
    """
    Order Block detection.
    
    An order block is a strong candle (large range) followed by a move in the same direction.
    Represents institutional buying/selling zone.
    
    Bullish OB: Strong green candle before upward move
    Bearish OB: Strong red candle before downward move
    
    Args:
        df: DataFrame with OHLC data
        strength_threshold: Minimum candle size as fraction of price
    
    Returns:
        DataFrame with order block columns added
    """
    df = df.copy()
    
    # Candle strength (range relative to close)
    candle_range = df['high'] - df['low']
    candle_strength = candle_range / df['close']
    
    # Direction
    bullish_candle = df['close'] > df['open']
    bearish_candle = df['close'] < df['open']
    
    # Strong candles
    strong_bullish = bullish_candle & (candle_strength > strength_threshold)
    strong_bearish = bearish_candle & (candle_strength > strength_threshold)
    
    # Order block: strong candle followed by move in same direction
    next_move_up = df['close'].shift(-1) > df['close']
    next_move_down = df['close'].shift(-1) < df['close']
    
    df['order_block_bullish'] = (strong_bullish & next_move_up).astype(int)
    df['order_block_bearish'] = (strong_bearish & next_move_down).astype(int)
    df['order_block_strength'] = np.where(df['order_block_bullish'] | df['order_block_bearish'],
                                           candle_strength, 0)
    
    # Rolling count
    df['order_block_count'] = (df['order_block_bullish'] + df['order_block_bearish']).rolling(20).sum()
    
    return df


def add_premium_discount_zones(df: pd.DataFrame, lookback: int = 50) -> pd.DataFrame:
    """
    Premium/Discount zone calculation.
    
    Divides recent range into zones:
    - Premium: Upper 50% (resistance, better to sell)
    - Discount: Lower 50% (support, better to buy)
    - Equilibrium: Middle (neutral)
    
    Args:
        df: DataFrame with close prices
        lookback: Bars to calculate range (default 50 = ~12.5 hours on 15m)
    
    Returns:
        DataFrame with premium/discount columns
    """
    df = df.copy()
    
    # Recent range
    range_high = df['high'].rolling(lookback).max()
    range_low = df['low'].rolling(lookback).min()
    range_mid = (range_high + range_low) / 2
    
    # Position within range (0 = low, 1 = high)
    range_position = (df['close'] - range_low) / (range_high - range_low)
    
    df['premium_discount_position'] = range_position
    df['in_premium'] = (df['close'] > range_mid).astype(int)
    df['in_discount'] = (df['close'] < range_mid).astype(int)
    df['distance_from_equilibrium'] = (df['close'] - range_mid) / df['close']
    
    return df


def add_market_structure(df: pd.DataFrame, swing_window: int = 10) -> pd.DataFrame:
    """
    Market structure analysis.
    
    Identifies higher highs, higher lows (uptrend) vs lower highs, lower lows (downtrend).
    
    Args:
        df: DataFrame with OHLC data
        swing_window: Window for identifying swing points
    
    Returns:
        DataFrame with market structure columns
    """
    df = df.copy()
    
    # Swing highs and lows
    swing_high = df['high'].rolling(swing_window, center=True).max()
    swing_low = df['low'].rolling(swing_window, center=True).min()
    
    # Is current bar a swing high/low?
    is_swing_high = df['high'] == swing_high
    is_swing_low = df['low'] == swing_low
    
    # Higher high: current swing high > previous swing high
    prev_swing_high = swing_high.shift(swing_window)
    higher_high = is_swing_high & (df['high'] > prev_swing_high)
    
    # Lower low: current swing low < previous swing low
    prev_swing_low = swing_low.shift(swing_window)
    lower_low = is_swing_low & (df['low'] < prev_swing_low)
    
    # Higher low
    higher_low = is_swing_low & (df['low'] > prev_swing_low)
    
    # Lower high
    lower_high = is_swing_high & (df['high'] < prev_swing_high)
    
    df['higher_high'] = higher_high.astype(int)
    df['higher_low'] = higher_low.astype(int)
    df['lower_high'] = lower_high.astype(int)
    df['lower_low'] = lower_low.astype(int)
    
    # Trend classification (rolling sum)
    df['bullish_structure'] = (df['higher_high'] + df['higher_low']).rolling(20).sum()
    df['bearish_structure'] = (df['lower_high'] + df['lower_low']).rolling(20).sum()
    
    return df


def add_all_smc_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add all Smart Money Concepts features.
    
    This is the complete SMC feature set to enhance your existing volume features.
    
    Args:
        df: DataFrame with OHLC data
    
    Returns:
        DataFrame with all SMC features added
    """
    df = df.copy()
    
    # Core SMC patterns
    df = detect_fair_value_gaps(df, threshold=0.0005)
    df = detect_break_of_structure(df, lookback=20)
    df = detect_liquidity_sweeps(df, lookback=10, sweep_threshold=0.0002)
    df = detect_order_blocks(df, strength_threshold=0.0015)
    
    # Positional analysis
    df = add_premium_discount_zones(df, lookback=50)
    df = add_market_structure(df, swing_window=10)
    
    return df


if __name__ == "__main__":
    # Test SMC features
    print("Testing SMC features...")
    
    # Create sample data
    dates = pd.date_range('2024-01-01', periods=1000, freq='15min')
    np.random.seed(42)
    
    # Simulate trending data with gaps
    trend = np.linspace(1800, 1900, 1000)
    noise = np.random.randn(1000) * 5
    close = trend + noise
    
    df = pd.DataFrame({
        'open': close - np.random.rand(1000) * 2,
        'high': close + np.random.rand(1000) * 5,
        'low': close - np.random.rand(1000) * 5,
        'close': close,
        'volume': np.random.randint(100, 1000, 1000)
    }, index=dates)
    
    # Add SMC features
    df = add_all_smc_features(df)
    
    print(f"\nOriginal columns: 5")
    print(f"After SMC features: {len(df.columns)} columns")
    
    smc_cols = [c for c in df.columns if c not in ['open', 'high', 'low', 'close', 'volume']]
    print(f"\nNew SMC feature columns ({len(smc_cols)}):")
    for col in smc_cols:
        print(f"  - {col}")
    
    print(f"\nSample statistics:")
    print(f"Bullish FVGs detected: {df['fvg_bullish'].sum()}")
    print(f"Bearish FVGs detected: {df['fvg_bearish'].sum()}")
    print(f"Bullish BOS detected: {df['bos_bullish'].sum()}")
    print(f"Liquidity sweeps detected: {df['liquidity_sweep_count'].max()}")
    print(f"Order blocks detected: {df['order_block_count'].max()}")
