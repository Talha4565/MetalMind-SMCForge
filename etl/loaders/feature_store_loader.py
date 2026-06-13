"""Load features into file-based feature store."""

import pandas as pd
import pickle
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from .base import BaseLoader
from ..exceptions import LoadError
import logging

logger = logging.getLogger(__name__)


class FeatureStoreLoader(BaseLoader):
    """Load features into file-based feature store."""
    
    def __init__(
        self,
        store_path: str,
        asset: str,
        version: bool = True,
        format: str = 'parquet',  # 'parquet' or 'csv'
        **kwargs
    ):
        super().__init__(kwargs)
        self.store_path = Path(store_path)
        self.asset = asset
        self.version = version
        self.format = format.lower()
        
        # Create store directory if it doesn't exist
        try:
            self.store_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Feature store directory: {self.store_path}")
        except Exception as e:
            raise LoadError(f"Failed to create feature store directory: {str(e)}")
    
    def load(self, data: pd.DataFrame) -> bool:
        """Save features to feature store."""
        if data.empty:
            logger.warning("Attempting to load empty DataFrame - skipping")
            return True
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Generate filename
            if self.version:
                filename = f"{self.asset}_features_{timestamp}.{self.format}"
            else:
                filename = f"{self.asset}_features_latest.{self.format}"
            
            filepath = self.store_path / filename
            
            # Save based on format
            if self.format == 'parquet':
                data.to_parquet(filepath, index=False)
            elif self.format == 'csv':
                data.to_csv(filepath, index=False)
            else:
                raise LoadError(f"Unsupported format: {self.format}")
            
            logger.info(f"Features saved to {filepath}")
            
            # Always save as 'latest' for easy access
            latest_path = self.store_path / f"{self.asset}_features_latest.{self.format}"
            if self.version and latest_path != filepath:
                if self.format == 'parquet':
                    data.to_parquet(latest_path, index=False)
                else:
                    data.to_csv(latest_path, index=False)
                logger.info(f"Updated latest features: {latest_path}")
            
            # Save metadata
            metadata = {
                'asset': self.asset,
                'timestamp': timestamp,
                'rows': len(data),
                'columns': list(data.columns),
                'filepath': str(filepath),
                'format': self.format,
                'created_at': datetime.now().isoformat()
            }
            
            meta_path = self.store_path / f"{self.asset}_metadata.pkl"
            with open(meta_path, 'wb') as f:
                pickle.dump(metadata, f)
            
            logger.info(f"Metadata saved to {meta_path}")
            return True
            
        except Exception as e:
            logger.error(f"Feature store load failed: {e}")
            raise LoadError(f"Failed to save features: {str(e)}")
    
    def get_latest(self) -> Optional[pd.DataFrame]:
        """Retrieve latest features."""
        latest_path = self.store_path / f"{self.asset}_features_latest.{self.format}"
        
        if not latest_path.exists():
            logger.warning(f"Latest features not found: {latest_path}")
            return None
        
        try:
            if self.format == 'parquet':
                df = pd.read_parquet(latest_path)
            else:
                df = pd.read_csv(latest_path)
            
            logger.info(f"Loaded {len(df)} rows from {latest_path}")
            return df
            
        except Exception as e:
            logger.error(f"Failed to load latest features: {e}")
            return None
    
    def get_metadata(self) -> Optional[Dict[str, Any]]:
        """Retrieve feature metadata."""
        meta_path = self.store_path / f"{self.asset}_metadata.pkl"
        
        if not meta_path.exists():
            return None
        
        try:
            with open(meta_path, 'rb') as f:
                metadata = pickle.load(f)
            return metadata
        except Exception as e:
            logger.error(f"Failed to load metadata: {e}")
            return None
    
    def list_versions(self) -> list:
        """List all versioned feature files."""
        pattern = f"{self.asset}_features_*.{self.format}"
        files = sorted(self.store_path.glob(pattern), reverse=True)
        
        # Exclude 'latest' file
        files = [f for f in files if 'latest' not in f.name]
        
        return [str(f) for f in files]
