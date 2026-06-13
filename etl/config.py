"""ETL Pipeline Configuration."""

from dataclasses import dataclass
from pathlib import Path
import os


@dataclass
class ETLConfig:
    """ETL Pipeline Configuration."""
    
    # Data Sources
    gold_data_path: str = 'Gold Dataset/Gold_15m_Candlestick.csv'
    silver_data_path: str = 'Silver Dataset/Silver_15m_Candlestick.csv'
    
    # Database
    database_url: str = 'sqlite:///instance/metalmind_smc.db'
    
    # Feature Store
    feature_store_path: str = 'data/features'
    
    # API Configuration (if using live data)
    api_base_url: str = os.getenv('PRICE_API_URL', '')
    api_key: str = os.getenv('PRICE_API_KEY', '')
    
    # Scheduling
    schedule_interval_minutes: int = 15
    
    # Processing
    batch_size: int = 1000
    max_retries: int = 3
    
    # Data Quality
    handle_missing: str = 'ffill'  # 'ffill', 'bfill', or 'drop'
    remove_outliers: bool = True
    outlier_std: float = 5.0
    
    # Feature Engineering
    include_labels: bool = True
    label_threshold: float = 0.002
    label_lookahead: int = 12
    
    # Logging
    log_level: str = 'INFO'
    log_dir: str = 'logs'
    
    @classmethod
    def from_env(cls) -> 'ETLConfig':
        """Create config from environment variables."""
        return cls(
            gold_data_path=os.getenv('GOLD_DATA_PATH', cls.gold_data_path),
            silver_data_path=os.getenv('SILVER_DATA_PATH', cls.silver_data_path),
            database_url=os.getenv('DATABASE_URL', cls.database_url),
            feature_store_path=os.getenv('FEATURE_STORE_PATH', cls.feature_store_path),
            schedule_interval_minutes=int(os.getenv('SCHEDULE_INTERVAL', cls.schedule_interval_minutes)),
        )
    
    def validate(self) -> bool:
        """Validate configuration."""
        errors = []
        
        # Check if data files exist
        if self.gold_data_path and not Path(self.gold_data_path).exists():
            errors.append(f"Gold data file not found: {self.gold_data_path}")
        
        if self.silver_data_path and not Path(self.silver_data_path).exists():
            errors.append(f"Silver data file not found: {self.silver_data_path}")
        
        # Check feature store path
        feature_path = Path(self.feature_store_path)
        if not feature_path.exists():
            feature_path.mkdir(parents=True, exist_ok=True)
        
        # Check log directory
        log_path = Path(self.log_dir)
        if not log_path.exists():
            log_path.mkdir(parents=True, exist_ok=True)
        
        if errors:
            for error in errors:
                print(f"Configuration Error: {error}")
            return False
        
        return True
