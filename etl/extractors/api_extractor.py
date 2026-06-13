"""Extract data from price API."""

import pandas as pd
import requests
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from .base import BaseExtractor
from ..exceptions import ExtractionError, ValidationError
import logging
import time

logger = logging.getLogger(__name__)


class APIExtractor(BaseExtractor):
    """Extract data from price API."""
    
    def __init__(
        self,
        base_url: str,
        asset: str,
        api_key: Optional[str] = None,
        lookback_days: int = 30,
        **kwargs
    ):
        super().__init__(kwargs)
        self.base_url = base_url
        self.asset = asset
        self.api_key = api_key
        self.lookback_days = lookback_days
        self.max_retries = 3
        self.retry_delay = 5
    
    def extract(self) -> pd.DataFrame:
        """Fetch data from API with retry logic."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.lookback_days)
        
        params = {
            'symbol': self.asset,
            'from': start_date.strftime('%Y-%m-%d'),
            'to': end_date.strftime('%Y-%m-%d'),
        }
        
        headers = {}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Fetching {self.asset} data from API (attempt {attempt + 1}/{self.max_retries})")
                
                response = requests.get(
                    self.base_url,
                    params=params,
                    headers=headers,
                    timeout=30
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Handle different API response formats
                if isinstance(data, dict):
                    if 'prices' in data:
                        df = pd.DataFrame(data['prices'])
                    elif 'data' in data:
                        df = pd.DataFrame(data['data'])
                    else:
                        df = pd.DataFrame([data])
                else:
                    df = pd.DataFrame(data)
                
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                logger.info(f"Successfully fetched {len(df)} records from API")
                return df
                
            except requests.RequestException as e:
                logger.warning(f"API request failed (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    logger.info(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    raise ExtractionError(f"API extraction failed after {self.max_retries} attempts: {str(e)}")
            
            except Exception as e:
                raise ExtractionError(f"Failed to parse API response: {str(e)}")
    
    def validate(self, data: pd.DataFrame) -> bool:
        """Validate API response data."""
        if data.empty:
            raise ValidationError("API returned empty dataset")
        
        required = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        missing = set(required) - set(data.columns)
        
        if missing:
            logger.error(f"API response missing columns: {missing}")
            raise ValidationError(f"API response missing columns: {missing}")
        
        # Check for null values in critical columns
        for col in ['open', 'high', 'low', 'close']:
            null_count = data[col].isnull().sum()
            if null_count > 0:
                logger.warning(f"Column '{col}' has {null_count} null values")
        
        return True
