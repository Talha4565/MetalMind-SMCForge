"""Abstract base class for all loaders."""

from abc import ABC, abstractmethod
from typing import Any, Dict
import logging
import pandas as pd

logger = logging.getLogger(__name__)


class BaseLoader(ABC):
    """Abstract base class for all loaders."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.records_loaded = 0
    
    @abstractmethod
    def load(self, data: pd.DataFrame) -> bool:
        """Load data to destination. Must be implemented by subclasses."""
        pass
    
    def run(self, data: pd.DataFrame) -> bool:
        """Execute load with logging."""
        logger.info(f"Starting load: {self.__class__.__name__}")
        
        success = self.load(data)
        self.records_loaded = len(data) if success else 0
        
        logger.info(f"Load complete: {self.records_loaded} records")
        return success
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get loader metadata."""
        return {
            'loader': self.__class__.__name__,
            'records_loaded': self.records_loaded,
        }
