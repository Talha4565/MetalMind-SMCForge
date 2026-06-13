"""Demo configuration for fast ETL execution (10K rows)."""

from .config import ETLConfig


class DemoETLConfig(ETLConfig):
    """ETL Configuration for Demo/Testing - Uses last 10K rows for speed."""
    
    # Data Sources (same)
    gold_data_path: str = 'Gold Dataset/Gold_15m_Candlestick.csv'
    silver_data_path: str = 'Silver Dataset/Silver_15m_Candlestick.csv'
    
    # Demo Settings
    max_rows: int = 10000  # Only process last 10K rows
    
    # Faster processing
    batch_size: int = 5000
    
    # Data Quality (same)
    handle_missing: str = 'ffill'
    remove_outliers: bool = True
    outlier_std: float = 5.0
    
    # Feature Engineering
    include_labels: bool = True
    label_threshold: float = 0.002
    label_lookahead: int = 12
    
    # Database (demo tables)
    database_url: str = 'sqlite:///instance/metalmind_smc_demo.db'
    
    # Feature Store
    feature_store_path: str = 'data/features_demo'
