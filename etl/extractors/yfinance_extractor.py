"""Extract market data from Yahoo Finance via yfinance."""

import pandas as pd
import numpy as np
from typing import Dict, Any
from datetime import datetime, timedelta
from .base import BaseExtractor
from ..exceptions import ExtractionError, ValidationError
import logging

logger = logging.getLogger(__name__)

# yfinance interval limits
INTERVAL_LIMITS = {
    '5m': {'period': '60d', 'max_rows': 13500},
    '15m': {'period': '60d', 'max_rows': 4500},
    '30m': {'period': '60d', 'max_rows': 2300},
    '1h': {'period': '730d', 'max_rows': 14000},
    '1d': {'period': 'max', 'max_rows': 7000},
}

# Yahoo Finance ticker symbols
TICKER_MAP = {
    'gold': 'GC=F',
    'silver': 'SI=F',
}


class YFinanceExtractor(BaseExtractor):
    """Extract OHLCV data from Yahoo Finance."""
    
    def __init__(
        self,
        asset: str,
        intervals: list = None,
        **kwargs
    ):
        super().__init__(kwargs)
        self.asset = asset
        self.ticker = TICKER_MAP.get(asset)
        self.intervals = intervals or ['5m', '15m', '30m', '1h']
        self.metadata = {}
        
        if not self.ticker:
            raise ValueError(f"Unknown asset: {asset}. Supported: {list(TICKER_MAP.keys())}")
    
    def extract(self) -> Dict[str, pd.DataFrame]:
        """Fetch data for all intervals. Returns dict of interval -> DataFrame."""
        import yfinance as yf
        
        results = {}
        
        for interval in self.intervals:
            try:
                limit = INTERVAL_LIMITS.get(interval, {'period': '60d'})
                
                logger.info(f"Fetching {self.asset} {interval} data from yfinance...")
                ticker = yf.Ticker(self.ticker)
                df = ticker.history(period=limit['period'], interval=interval)
                
                if df.empty:
                    logger.warning(f"No data returned for {self.asset} {interval}")
                    continue
                
                # Reset index to get Date as column
                df = df.reset_index()
                
                # Handle both 'Datetime' and 'Date' column names from yfinance
                datetime_col = 'Datetime' if 'Datetime' in df.columns else 'Date'
                
                # Rename columns to match our CSV format
                df = df.rename(columns={
                    datetime_col: 'DateTime',
                    'Open': 'open',
                    'High': 'high',
                    'Low': 'low',
                    'Close': 'close',
                    'Volume': 'volume',
                })
                
                # Extract Date and Time from DateTime (matching CSV format)
                df['Date'] = pd.to_datetime(df['DateTime']).dt.strftime('%Y.%m.%d')
                df['Time'] = pd.to_datetime(df['DateTime']).dt.strftime('%H:%M')
                
                # Select and order columns to match CSV format
                df = df[['Date', 'Time', 'open', 'high', 'low', 'close', 'volume']]
                
                # Capitalize column names to match CSV
                df = df.rename(columns={
                    'open': 'Open',
                    'high': 'High',
                    'low': 'Low',
                    'close': 'Close',
                    'volume': 'Volume',
                })
                
                results[interval] = df
                logger.info(f"Fetched {len(df)} {interval} bars for {self.asset}")
                
            except Exception as e:
                logger.error(f"Failed to fetch {self.asset} {interval}: {e}")
                continue
        
        self.metadata = {
            'asset': self.asset,
            'ticker': self.ticker,
            'intervals': list(results.keys()),
            'total_rows': sum(len(df) for df in results.values()),
        }
        
        return results
    
    def validate(self, data: Dict[str, pd.DataFrame]) -> bool:
        """Validate extracted data."""
        if not data:
            raise ValidationError("No data extracted for any interval")
        
        for interval, df in data.items():
            required = ['Date', 'Time', 'Open', 'High', 'Low', 'Close', 'Volume']
            missing = set(required) - set(df.columns)
            if missing:
                raise ValidationError(f"Missing columns in {interval}: {missing}")
            
            if df.empty:
                raise ValidationError(f"Empty dataset for {interval}")
        
        return True
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get extraction metadata."""
        return self.metadata
