"""
Complete feature engineering pipeline.
Orchestrates volume features + SMC features + multi-timeframe features.
"""

import pandas as pd
import logging
from .volume_features import add_all_volume_features
from .smc_features import add_all_smc_features
from .multi_timeframe import add_all_multi_timeframe_features
from .labels import generate_labels

logger = logging.getLogger(__name__)


def engineer_all_features(df: pd.DataFrame, add_labels: bool = True) -> pd.DataFrame:
    """
    Apply complete feature engineering pipeline.
    
    Pipeline:
    1. Volume-based microstructure features (your existing baseline)
    2. Smart Money Concepts features (NEW)
    3. Multi-timeframe features (NEW)
    4. Label generation (optional)
    
    Args:
        df: Raw DataFrame with OHLC data (can be multi-timeframe aligned)
        add_labels: Whether to generate target labels
    
    Returns:
        DataFrame with all features engineered
    """
    logger.info("Starting feature engineering pipeline...")
    
    original_cols = len(df.columns)
    
    # 1. Volume features (proven baseline)
    logger.info("Adding volume microstructure features...")
    df = add_all_volume_features(df, windows=[4, 16, 96])
    
    # 2. SMC features (new enhancement)
    logger.info("Adding Smart Money Concepts features...")
    df = add_all_smc_features(df)
    
    # 3. Multi-timeframe features (if available)
    if any(col.startswith(('5m_', '30m_', '1h_')) for col in df.columns):
        logger.info("Adding multi-timeframe features...")
        df = add_all_multi_timeframe_features(df)
    else:
        logger.info("No multi-timeframe data detected, skipping MTF features")
    
    # 4. Labels (if requested)
    if add_labels:
        logger.info("Generating target labels...")
        df['target'] = generate_labels(df)
    
    # Drop NaNs from feature computation
    df.dropna(inplace=True)
    
    final_cols = len(df.columns)
    logger.info(f"Feature engineering complete: {original_cols} → {final_cols} columns "
                f"({final_cols - original_cols} new features)")
    
    return df


if __name__ == "__main__":
    print("Feature engineering pipeline ready.")
    print("Use engineer_all_features(df) to apply complete pipeline.")
