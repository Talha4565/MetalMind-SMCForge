"""Abstract base class for all extractors."""

from abc import ABC, abstractmethod
from typing import Any, Dict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BaseExtractor(ABC):
    """Abstract base class for all extractors."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.last_run = None
        self.records_extracted = 0
    
    @abstractmethod
    def extract(self) -> Any:
        """Extract data from source. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def validate(self, data: Any) -> bool:
        """Validate extracted data. Must be implemented by subclasses."""
        pass
    
    def run(self) -> Any:
        """Execute extraction with logging and error handling."""
        logger.info(f"Starting extraction: {self.__class__.__name__}")
        start_time = datetime.now()
        
        try:
            data = self.extract()
            
            if not self.validate(data):
                raise ValueError("Data validation failed")
            
            self.last_run = datetime.now()
            self.records_extracted = len(data) if hasattr(data, '__len__') else 1
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"Extraction complete: {self.records_extracted} records in {duration:.2f}s")
            
            return data
            
        except Exception as e:
            logger.error(f"Extraction failed: {str(e)}")
            raise
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get extraction metadata."""
        return {
            'extractor': self.__class__.__name__,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'records_extracted': self.records_extracted,
        }
