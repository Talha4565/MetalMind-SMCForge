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
    Generate trading labels using triple-barrier method.
    
    For each bar, look ahead up to max_bars:
    - Label = 1 if price hits take_profit before stop_loss or timeout
    - Label = 0 otherwise
    
    Args:
        df: DataFrame with 'close' column
        take_profit_pct: Take profit threshold (default from asset-specific config)
        stop_loss_pct: Stop loss threshold (default from asset-specific config)
        max_bars: Maximum bars to look ahead (default from config: 6)
        asset: Asset name ("gold" or "silver") for asset-specific thresholds
    
    Returns:
        Series of binary labels (1 = trade signal, 0 = no trade)
    """
    params = get_label_params(asset)
    
    tp = take_profit_pct or params['take_profit_pct']
    sl = stop_loss_pct or params['stop_loss_pct']
    max_bars = max_bars or params['max_bars']
    
    close = df['close'].to_numpy()
    labels = np.zeros(len(close))
    
    for i in range(len(close) - max_bars):
        entry_price = close[i]
        
        for k in range(1, max_bars + 1):
            if i + k >= len(close):
                break
            
            future_price = close[i + k]
            ret = (future_price - entry_price) / entry_price
            
            # Hit take profit → label = 1
            if ret >= tp:
                labels[i] = 1
                break
            
            # Hit stop loss → label = 0
            if ret <= -sl:
                labels[i] = 0
                break
        else:
            # Timeout without hitting either barrier → label = 0 (no trade)
            labels[i] = 0
    
    return pd.Series(labels, index=df.index, name='target')


if __name__ == "__main__":
    print("Label generation module loaded.")
    print(f"Default params: {get_label_params()}")
