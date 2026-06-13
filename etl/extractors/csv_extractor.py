"""Extract data from CSV files."""

import pandas as pd
from pathlib import Path
from typing import Optional, List
from .base import BaseExtractor
from ..exceptions import ExtractionError, ValidationError
import logging

logger = logging.getLogger(__name__)


class CSVExtractor(BaseExtractor):
    """Extract data from CSV files."""
    
    def __init__(
        self,
        file_path: str,
        date_column: str = 'timestamp',
        required_columns: List[str] = None,
        max_rows: int = None,
        **kwargs
    ):
        super().__init__(kwargs)
        self.file_path = Path(file_path)
        self.date_column = date_column
        self.required_columns = required_columns or ['open', 'high', 'low', 'close', 'volume']
        self.max_rows = max_rows  # Limit rows for testing/demo
    
    def extract(self) -> pd.DataFrame:
        """Read CSV file into DataFrame."""
        if not self.file_path.exists():
            raise ExtractionError(f"CSV file not found: {self.file_path}")
        
        try:
            df = pd.read_csv(self.file_path)
            
            # Handle different date column formats
            if 'Date' in df.columns and 'Time' in df.columns:
                # Combine Date and Time columns
                df['timestamp'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
                df = df.drop(['Date', 'Time'], axis=1)
            elif self.date_column in df.columns:
                df['timestamp'] = pd.to_datetime(df[self.date_column])
            else:
                raise ExtractionError(f"Date column '{self.date_column}' not found in CSV")
            
            # Standardize column names to lowercase
            df.columns = df.columns.str.lower()
            
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            # Limit rows if max_rows specified (for demo/testing)
            if self.max_rows and len(df) > self.max_rows:
                logger.info(f"Limiting to last {self.max_rows} rows (from {len(df)})")
                df = df.tail(self.max_rows).reset_index(drop=True)
            
            logger.info(f"Extracted {len(df)} rows from {self.file_path.name}")
            return df
            
        except Exception as e:
            raise ExtractionError(f"Failed to read CSV file: {str(e)}")
    
    def validate(self, data: pd.DataFrame) -> bool:
        """Validate extracted data."""
        if data.empty:
            logger.warning("Extracted DataFrame is empty")
            raise ValidationError("Extracted DataFrame is empty")
        
        # Check required columns
        missing_cols = set(self.required_columns) - set(data.columns)
        if missing_cols:
            logger.error(f"Missing required columns: {missing_cols}")
            raise ValidationError(f"Missing required columns: {missing_cols}")
        
        # Check date column
        if self.date_column not in data.columns:
            raise ValidationError(f"Date column '{self.date_column}' not found")
        
        if data[self.date_column].isnull().any():
            logger.error("Date column contains null values")
            raise ValidationError("Date column contains null values")
        
        # Check for duplicate timestamps
        duplicates = data[self.date_column].duplicated().sum()
        if duplicates > 0:
            logger.warning(f"Found {duplicates} duplicate timestamps")
        
        return True
