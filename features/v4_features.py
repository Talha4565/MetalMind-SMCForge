"""
V4-specific feature computation for inference.
Computes features that the standard pipeline doesn't produce but V4 model expects.
"""

import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


def compute_v4_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute V4-specific features on a 15m DataFrame that has been aligned
    with 30m and 1h data via MultiTimeframeLoader.

    Expects columns: open, high, low, close, volume,
    30m_open/30m_high/30m_low/30m_close/30m_volume,
    1h_open/1h_high/1h_low/1h_close/1h_volume.

    Adds: cvd_15m, cvd_15m_slope, cvd_30m, cvd_30m_slope,
    adx_14, adx_trending, atr_14,
    trend_ema_cross, trend_price_vs_ema, trend_adx, trend_strength,
    htf_30m_*, htf_1h_*.
    """
    df = df.copy()

    # ── CVD (Cumulative Volume Delta) approximation ──
    # Use (close - open) / (high - low) * volume as delta proxy
    df['delta'] = np.where(
        df['high'] != df['low'],
        ((df['close'] - df['open']) / (df['high'] - df['low'])) * df['volume'],
        0
    )
    df['cvd_15m'] = df['delta'].cumsum()
    df['cvd_15m_slope'] = df['cvd_15m'].diff(4)  # slope over 4 bars (1h)

    # 30m CVD
    if '30m_close' in df.columns:
        hl_30m = df['30m_high'] - df['30m_low']
        df['delta_30m'] = np.where(
            hl_30m != 0,
            ((df['30m_close'] - df['30m_open']) / hl_30m) * df['30m_volume'],
            0
        )
        df['cvd_30m'] = df['delta_30m'].cumsum()
        df['cvd_30m_slope'] = df['cvd_30m'].diff(2)  # slope over 2 bars
    else:
        df['cvd_30m'] = 0.0
        df['cvd_30m_slope'] = 0.0

    # ── ATR (Average True Range) ──
    high_low = df['high'] - df['low']
    high_close = (df['high'] - df['close'].shift(1)).abs()
    low_close = (df['low'] - df['close'].shift(1)).abs()
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['atr_14'] = true_range.rolling(14).mean()

    # ── ADX (Average Directional Index) ──
    plus_dm = df['high'].diff()
    minus_dm = -df['low'].diff()
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)

    atr_smooth = true_range.rolling(14).mean()
    plus_di = 100 * (plus_dm.rolling(14).mean() / atr_smooth)
    minus_di = 100 * (minus_dm.rolling(14).mean() / atr_smooth)
    dx = 100 * ((plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, 1e-10))
    df['adx_14'] = dx.rolling(14).mean()
    df['adx_trending'] = (df['adx_14'] > 25).astype(float)

    # ── Trend features (EMA crossover) ──
    ema_20 = df['close'].ewm(span=20, adjust=False).mean()
    ema_50 = df['close'].ewm(span=50, adjust=False).mean()
    df['trend_ema_cross'] = (ema_20 > ema_50).astype(int)
    df['trend_price_vs_ema'] = (df['close'] - ema_20) / ema_20
    df['trend_adx'] = df['adx_14'] / 100.0  # normalized
    df['trend_strength'] = ((ema_20 - ema_50).abs() / ema_50).fillna(0)

    # ── HTF 30m indicators ──
    if '30m_close' in df.columns:
        df['htf_30m_trend'] = (df['30m_close'].ewm(span=10, adjust=False).mean() >
                               df['30m_close'].ewm(span=30, adjust=False).mean()).astype(int)
        htf30_atr = (df['30m_high'] - df['30m_low']).rolling(14).mean()
        df['htf_30m_atr'] = htf30_atr / df['30m_close']
        htf30_rsi_delta = df['30m_close'].diff()
        htf30_gain = htf30_rsi_delta.clip(lower=0).rolling(14).mean()
        htf30_loss = (-htf30_rsi_delta.clip(upper=0)).rolling(14).mean()
        df['htf_30m_rsi'] = 100 - 100 / (1 + htf30_gain / htf30_loss.replace(0, 1e-10))
        df['htf_30m_dist_high'] = (df['30m_high'].rolling(20).max() - df['30m_close']) / df['30m_close']
        df['htf_30m_dist_low'] = (df['30m_close'] - df['30m_low'].rolling(20).min()) / df['30m_close']
        df['htf_30m_momentum'] = df['30m_close'].pct_change(5)
    else:
        for col in ['htf_30m_trend', 'htf_30m_atr', 'htf_30m_rsi',
                     'htf_30m_dist_high', 'htf_30m_dist_low', 'htf_30m_momentum']:
            df[col] = 0.0

    # ── HTF 1h indicators ──
    if '1h_close' in df.columns:
        df['htf_1h_trend'] = (df['1h_close'].ewm(span=10, adjust=False).mean() >
                              df['1h_close'].ewm(span=30, adjust=False).mean()).astype(int)
        htf1h_atr = (df['1h_high'] - df['1h_low']).rolling(14).mean()
        df['htf_1h_atr'] = htf1h_atr / df['1h_close']
        htf1h_rsi_delta = df['1h_close'].diff()
        htf1h_gain = htf1h_rsi_delta.clip(lower=0).rolling(14).mean()
        htf1h_loss = (-htf1h_rsi_delta.clip(upper=0)).rolling(14).mean()
        df['htf_1h_rsi'] = 100 - 100 / (1 + htf1h_gain / htf1h_loss.replace(0, 1e-10))
        df['htf_1h_dist_high'] = (df['1h_high'].rolling(20).max() - df['1h_close']) / df['1h_close']
        df['htf_1h_dist_low'] = (df['1h_close'] - df['1h_low'].rolling(20).min()) / df['1h_close']
        df['htf_1h_momentum'] = df['1h_close'].pct_change(5)
    else:
        for col in ['htf_1h_trend', 'htf_1h_atr', 'htf_1h_rsi',
                     'htf_1h_dist_high', 'htf_1h_dist_low', 'htf_1h_momentum']:
            df[col] = 0.0

    # Clean up helper columns
    df.drop(columns=['delta', 'delta_30m'], errors='ignore', inplace=True)

    return df
