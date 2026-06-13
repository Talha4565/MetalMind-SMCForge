"""Transform raw OHLCV data into ML features using existing feature engineering modules."""

import pandas as pd
import numpy as np
from typing import Dict, Any, List
from .base import BaseTransformer
from ..exceptions import TransformationError
import logging
import sys
from pathlib import Path

# Add parent directory to path to import existing modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)


class FeatureTransformer(BaseTransformer):
    """Transform raw OHLCV data into ML features."""
    
    def __init__(
        self,
        asset: str = 'XAUUSD',
        include_labels: bool = True,
        label_config: Dict[str, Any] = None,
        **kwargs
    ):
        super().__init__(kwargs)
        self.asset = asset
        self.include_labels = include_labels
        self.label_config = label_config or {
            'threshold': 0.002,
            'lookahead': 12
        }
    
    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """Apply feature engineering pipeline."""
        if data.empty:
            raise TransformationError("Cannot transform empty DataFrame")
        
        df = data.copy()
        initial_rows = len(df)
        
        try:
            # Import your existing feature modules
            from features.smc_features import add_all_smc_features
            from features.multi_timeframe import add_all_multi_timeframe_features
            from features.volume_features import add_all_volume_features
            from features.labels import generate_labels
            
            # Set timestamp as index (required by feature functions)
            if 'timestamp' in df.columns and not isinstance(df.index, pd.DatetimeIndex):
                df = df.set_index('timestamp')
                logger.info("Set timestamp as DatetimeIndex")
            
            # Calculate SMC features
            logger.info("Calculating SMC features...")
            df = add_all_smc_features(df)
            
            # Calculate multi-timeframe features
            logger.info("Calculating multi-timeframe features...")
            df = add_all_multi_timeframe_features(df)
            
            # Calculate volume features
            logger.info("Calculating volume features...")
            df = add_all_volume_features(df)
            
            # Generate labels if requested
            if self.include_labels:
                logger.info("Generating labels...")
                df['label'] = generate_labels(
                    df,
                    max_bars=self.label_config['lookahead']
                )
            
            # Reset index before dropping NaN
            df = df.reset_index()
            
            # Drop rows with NaN values
            before_drop = len(df)
            df = df.dropna()
            dropped_rows = before_drop - len(df)
            
            if dropped_rows > 0:
                logger.info(f"Dropped {dropped_rows} rows with NaN values after feature engineering")
            
            final_rows = len(df)
            feature_count = len(df.columns)
            
            logger.info(f"Feature engineering complete: {initial_rows} -> {final_rows} rows, {feature_count} features")
            
            if final_rows == 0:
                raise TransformationError("All rows were dropped during feature engineering")
            
            return df
            
        except ImportError as e:
            logger.error(f"Failed to import feature engineering modules: {e}")
            raise TransformationError(f"Feature engineering modules not found: {str(e)}")
        
        except Exception as e:
            logger.error(f"Feature engineering failed: {e}")
            raise TransformationError(f"Feature engineering failed: {str(e)}")
    
    def get_feature_names(self) -> List[str]:
        """Return list of generated feature names."""
        if self.last_output is None:
            return []
        
        exclude = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'label']
        return [col for col in self.last_output.columns if col not in exclude]
    
    def get_feature_count(self) -> int:
        """Return number of features generated."""
        return len(self.get_feature_names())
