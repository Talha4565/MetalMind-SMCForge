"""
SHAP-based model explainability.
Provides feature importance and trade-level explanations.
"""

import pandas as pd
import numpy as np
import shap
import matplotlib.pyplot as plt
import logging
from pathlib import Path
from config.settings import SHAP_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ShapAnalyzer:
    """SHAP-based explainability for XGBoost models."""
    
    def __init__(self, model, sample_size: int = None):
        self.model = model
        self.sample_size = sample_size or SHAP_CONFIG['sample_size']
        self.explainer = None
        self.shap_values = None
        
    def compute_shap_values(self, X: pd.DataFrame):
        """Compute SHAP values for dataset."""
        logger.info(f"Computing SHAP values for {len(X)} samples...")
        
        # Sample if dataset is large
        if len(X) > self.sample_size:
            X_sample = X.sample(n=self.sample_size, random_state=42)
        else:
            X_sample = X
        
        # Create explainer
        self.explainer = shap.TreeExplainer(self.model)
        
        # Compute SHAP values
        self.shap_values = self.explainer.shap_values(X_sample)
        
        logger.info("SHAP values computed")
        return self.shap_values
    
    def plot_feature_importance(self, X: pd.DataFrame, top_n: int = None, save_path: Path = None):
        """Plot global feature importance."""
        if self.shap_values is None:
            self.compute_shap_values(X)
        
        top_n = top_n or SHAP_CONFIG['plot_top_n']
        
        plt.figure(figsize=(10, 8))
        shap.summary_plot(self.shap_values, X, plot_type="bar", max_display=top_n, show=False)
        plt.title(f"Top {top_n} Most Important Features (SHAP)")
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            logger.info(f"Saved feature importance plot to {save_path}")
        
        plt.show()
    
    def plot_summary(self, X: pd.DataFrame, top_n: int = None, save_path: Path = None):
        """Plot SHAP summary (beeswarm)."""
        if self.shap_values is None:
            self.compute_shap_values(X)
        
        top_n = top_n or SHAP_CONFIG['plot_top_n']
        
        plt.figure(figsize=(10, 8))
        shap.summary_plot(self.shap_values, X, max_display=top_n, show=False)
        plt.title(f"SHAP Summary Plot (Top {top_n} Features)")
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            logger.info(f"Saved summary plot to {save_path}")
        
        plt.show()
    
    def explain_prediction(self, X_row: pd.Series, save_path: Path = None):
        """Explain a single prediction with waterfall plot."""
        if self.explainer is None:
            self.explainer = shap.TreeExplainer(self.model)
        
        shap_value = self.explainer.shap_values(X_row.values.reshape(1, -1))
        
        plt.figure(figsize=(10, 6))
        shap.waterfall_plot(
            shap.Explanation(
                values=shap_value[0],
                base_values=self.explainer.expected_value,
                data=X_row.values,
                feature_names=X_row.index.tolist()
            ),
            show=False
        )
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            logger.info(f"Saved waterfall plot to {save_path}")
        
        plt.show()
    
    def get_top_features(self, n: int = 20) -> pd.DataFrame:
        """Get top N features by mean absolute SHAP value."""
        if self.shap_values is None:
            raise ValueError("SHAP values not computed yet. Call compute_shap_values() first.")
        
        mean_abs_shap = np.abs(self.shap_values).mean(axis=0)
        feature_importance = pd.DataFrame({
            'feature': self.explainer.feature_names,
            'importance': mean_abs_shap
        }).sort_values('importance', ascending=False)
        
        return feature_importance.head(n)


if __name__ == "__main__":
    print("SHAP analyzer ready.")
    print("Use ShapAnalyzer(model).compute_shap_values(X) to analyze model.")
