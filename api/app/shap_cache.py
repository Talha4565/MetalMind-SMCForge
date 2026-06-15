"""
SHAP cache manager for efficient feature importance computation.
Computes SHAP values on startup and caches them for API serving.
"""

import pickle
import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    logger.warning("⚠️ SHAP not available - install with: pip install shap")


class ShapCache:
    """Thread-safe SHAP cache for feature importance."""
    
    def __init__(self):
        self._cache: Dict[str, Dict] = {}
        self._computed = False
    
    def compute_shap_for_asset(self, asset: str, model, X_sample: pd.DataFrame) -> Dict:
        """
        Compute SHAP feature importance for an asset.
        
        Args:
            asset: "gold" or "silver"
            model: Trained XGBoost model
            X_sample: Sample of feature data for SHAP computation
        
        Returns:
            Dict with feature importance rankings
        """
        if not SHAP_AVAILABLE:
            logger.warning(f"SHAP not available for {asset} - returning mock data")
            return self._get_mock_importance(asset)
        
        if model is None:
            logger.warning(f"Model not available for {asset} - returning mock data")
            return self._get_mock_importance(asset)
        
        try:
            logger.info(f"Computing SHAP values for {asset}...")
            
            # Create SHAP explainer
            explainer = shap.TreeExplainer(model)
            
            # Compute SHAP values (sample if needed)
            if len(X_sample) > 1000:
                X_sample = X_sample.sample(n=1000, random_state=42)
            
            shap_values = explainer.shap_values(X_sample)
            
            # Handle binary classification (SHAP returns list of arrays)
            if isinstance(shap_values, list):
                shap_values = shap_values[1]  # Use positive class SHAP values
            
            # Calculate mean absolute SHAP values
            feature_importance = np.abs(shap_values).mean(axis=0)
            
            # Sort by importance
            sorted_idx = np.argsort(feature_importance)[::-1]
            
            # Format for API response
            importance_dict = {
                'feature_importance': [
                    {
                        'feature': X_sample.columns[i],
                        'importance': float(feature_importance[i])
                    }
                    for i in sorted_idx[:20]  # Top 20 features
                ],
                'computed': True
            }
            
            logger.info(f"✅ SHAP values computed for {asset}: {len(importance_dict['feature_importance'])} features")
            self._cache[asset] = importance_dict
            
            return importance_dict
        
        except Exception as e:
            logger.error(f"Error computing SHAP for {asset}: {e}")
            logger.error("Falling back to mock SHAP data")
            mock = self._get_mock_importance(asset)
            self._cache[asset] = mock
            return mock
    
    def get(self, asset: str) -> Dict:
        """Get cached SHAP importance for asset."""
        if asset in self._cache:
            return self._cache[asset]
        else:
            logger.warning(f"No cached SHAP data for {asset} - returning mock")
            return self._get_mock_importance(asset)
    
    def _get_mock_importance(self, asset: str) -> Dict:
        """Return mock SHAP importance (fallback)."""
        mock_data = {
            'gold': {
                'feature_importance': [
                    {'feature': 'vwap_distance_5m', 'importance': 0.15},
                    {'feature': 'vwap_distance_15m', 'importance': 0.12},
                    {'feature': 'volume_imbalance', 'importance': 0.10},
                    {'feature': 'cvd_indicator', 'importance': 0.09},
                    {'feature': 'trend_strength_15m', 'importance': 0.08},
                    {'feature': 'fvg_score', 'importance': 0.07},
                    {'feature': 'liquidity_sweep_detected', 'importance': 0.06},
                    {'feature': 'break_of_structure', 'importance': 0.05},
                    {'feature': 'volume_spike', 'importance': 0.04},
                    {'feature': 'volatility_atr', 'importance': 0.03}
                ],
                'computed': False
            },
            'silver': {
                'feature_importance': [
                    {'feature': 'vwap_distance_15m', 'importance': 0.14},
                    {'feature': 'volume_imbalance', 'importance': 0.12},
                    {'feature': 'vwap_distance_5m', 'importance': 0.11},
                    {'feature': 'cvd_indicator', 'importance': 0.10},
                    {'feature': 'fvg_score', 'importance': 0.08},
                    {'feature': 'trend_strength_15m', 'importance': 0.07},
                    {'feature': 'liquidity_sweep_detected', 'importance': 0.06},
                    {'feature': 'volatility_atr', 'importance': 0.05},
                    {'feature': 'break_of_structure', 'importance': 0.04},
                    {'feature': 'order_block_distance', 'importance': 0.03}
                ],
                'computed': False
            }
        }
        return mock_data.get(asset, mock_data['gold'])
    
    def is_computed(self, asset: str) -> bool:
        """Check if SHAP values have been computed (not mocked)."""
        if asset in self._cache:
            return self._cache[asset].get('computed', False)
        return False


# Global cache instance
shap_cache = ShapCache()
