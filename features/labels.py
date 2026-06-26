"""
Label generation for supervised learning.
Implements triple-barrier labeling with asymmetric risk/reward.
"""

import pandas as pd
import numpy as np
from config.settings import get_label_params


def generate_labels(df: pd.DataFrame,
                    take_profit_pct: float = None,
                    stop_loss_pct: float = None,
                    max_bars: int = None,
                    asset: str = "gold") -> pd.Series:
    """
    Generate trading labels using triple-barrier method (3-class).

    For each bar, look ahead up to max_bars:
    - Label =  1 (BUY)  if price hits take_profit before stop_loss or timeout
    - Label = -1 (SELL) if price hits stop_loss before take_profit or timeout
    - Label =  0 (HOLD) if neither barrier hit within max_bars

    Args:
        df: DataFrame with 'close', 'high', 'low' columns
        take_profit_pct: Take profit threshold (default from asset config)
        stop_loss_pct: Stop loss threshold (default from asset config)
        max_bars: Maximum bars to look ahead (default from config: 6)
        asset: Asset name ("gold" or "silver")

    Returns:
        Series of labels: 1=BUY, -1=SELL, 0=HOLD
    """
    params = get_label_params(asset)

    tp = take_profit_pct or params['take_profit_pct']
    sl = stop_loss_pct or params['stop_loss_pct']
    max_bars = max_bars or params['max_bars']

    close = df['close'].to_numpy()
    high = df['high'].to_numpy()
    low = df['low'].to_numpy()
    labels = np.zeros(len(close), dtype=int)

    for i in range(len(close) - max_bars):
        entry_price = close[i]

        for k in range(1, max_bars + 1):
            if i + k >= len(close):
                break

            ret_high = (high[i + k] - entry_price) / entry_price
            ret_low = (low[i + k] - entry_price) / entry_price

            hit_tp = ret_high >= tp
            hit_sl = ret_low <= -sl

            # Whichever barrier hit first wins
            if hit_tp and hit_sl:
                # Both hit on same bar — check which was hit first via close direction
                if close[i + k] >= entry_price:
                    labels[i] = 1   # BUY — price moved up
                else:
                    labels[i] = -1  # SELL — price moved down
            elif hit_tp:
                labels[i] = 1   # BUY
            elif hit_sl:
                labels[i] = -1  # SELL
        # else: labels[i] stays 0 (HOLD)

    return pd.Series(labels, index=df.index, name='target')


if __name__ == "__main__":
    print("Label generation module loaded.")
    print(f"Default params: {get_label_params()}")
