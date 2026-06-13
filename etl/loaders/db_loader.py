"""Load data into SQLite database."""

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from typing import Optional
from .base import BaseLoader
from ..exceptions import LoadError
import logging

logger = logging.getLogger(__name__)


class DatabaseLoader(BaseLoader):
    """Load data into SQLite database."""
    
    def __init__(
        self,
        connection_string: str,
        table_name: str,
        if_exists: str = 'append',
        **kwargs
    ):
        super().__init__(kwargs)
        self.connection_string = connection_string
        self.table_name = table_name
        self.if_exists = if_exists  # 'append', 'replace', or 'fail'
        
        try:
            self.engine = create_engine(connection_string)
            logger.info(f"Database connection established: {connection_string}")
        except Exception as e:
            raise LoadError(f"Failed to create database engine: {str(e)}")
    
    def load(self, data: pd.DataFrame) -> bool:
        """Load DataFrame into database table."""
        if data.empty:
            logger.warning("Attempting to load empty DataFrame - skipping")
            return True
        
        try:
            # Load data in chunks for better performance
            data.to_sql(
                name=self.table_name,
                con=self.engine,
                if_exists=self.if_exists,
                index=False,
                chunksize=1000
            )
            
            # Get total row count
            with self.engine.connect() as conn:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {self.table_name}"))
                count = result.scalar()
            
            logger.info(f"Loaded {len(data)} rows. Table '{self.table_name}' now has {count} total rows.")
            return True
            
        except Exception as e:
            logger.error(f"Database load failed: {e}")
            raise LoadError(f"Failed to load data into database: {str(e)}")
    
    def truncate(self) -> bool:
        """Clear table before loading."""
        try:
            with self.engine.connect() as conn:
                conn.execute(text(f"DELETE FROM {self.table_name}"))
                conn.commit()
            logger.info(f"Truncated table '{self.table_name}'")
            return True
        except Exception as e:
            logger.error(f"Truncate failed: {e}")
            return False
    
    def table_exists(self) -> bool:
        """Check if table exists."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(
                    f"SELECT name FROM sqlite_master WHERE type='table' AND name='{self.table_name}'"
                ))
                return result.fetchone() is not None
        except Exception:
            return False
    
    def get_row_count(self) -> int:
        """Get current row count in table."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {self.table_name}"))
                return result.scalar()
        except Exception:
            return 0
