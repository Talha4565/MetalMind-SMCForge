"""Load data by appending to existing CSV files."""

import pandas as pd
from typing import Dict, Any
from pathlib import Path
from .base import BaseLoader
from ..exceptions import LoadError
import logging

logger = logging.getLogger(__name__)


class CSVAppendLoader(BaseLoader):
    """Append new data to existing CSV files."""
    
    def __init__(
        self,
        output_dir: str,
        asset: str,
        date_column: str = 'Date',
        time_column: str = 'Time',
        **kwargs
    ):
        super().__init__(kwargs)
        self.output_dir = Path(output_dir)
        self.asset = asset
        self.date_column = date_column
        self.time_column = time_column
        self._dedup_count = 0
        self._data = None
    
    def load(self, data: Any) -> bool:
        """Load data - stores dict for run() to process."""
        self._data = data
        return True
    
    def run(self, data: Dict[str, pd.DataFrame]) -> bool:
        """
        Append new data to existing CSVs.
        
        Args:
            data: Dict of interval -> DataFrame (from YFinanceExtractor)
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        for interval, new_df in data.items():
            try:
                self._append_to_csv(interval, new_df)
            except Exception as e:
                logger.error(f"Failed to append {interval} data: {e}")
                return False
        
        return True
    
    def _append_to_csv(self, interval: str, new_df: pd.DataFrame):
        """Append new data to a CSV file, deduplicating by Date+Time."""
        csv_path = self.output_dir / f"{self.asset.title()}_{interval}_Candlestick.csv"
        
        if csv_path.exists():
            existing_df = pd.read_csv(csv_path)
            
            # Combine existing + new
            combined = pd.concat([existing_df, new_df], ignore_index=True)
            
            # Deduplicate by Date + Time (keep last occurrence)
            before_dedup = len(combined)
            combined = combined.drop_duplicates(
                subset=[self.date_column, self.time_column],
                keep='last'
            )
            self._dedup_count += before_dedup - len(combined)
            
            # Sort by Date + Time
            combined = combined.sort_values([self.date_column, self.time_column]).reset_index(drop=True)
            
            combined.to_csv(csv_path, index=False)
            logger.info(f"Appended to {csv_path.name}: {len(new_df)} new rows, "
                       f"{before_dedup - len(combined)} duplicates removed, "
                       f"total: {len(combined)} rows")
        else:
            new_df.to_csv(csv_path, index=False)
            logger.info(f"Created new {csv_path.name}: {len(new_df)} rows")
        
        self.records_loaded += len(new_df)
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get loader metadata."""
        return {
            'loader': self.__class__.__name__,
            'output_dir': str(self.output_dir),
            'asset': self.asset,
            'records_loaded': self.records_loaded,
            'duplicates_removed': self._dedup_count,
        }
