"""Abstract base class for all transformers."""

from abc import ABC, abstractmethod
from typing import Any, Dict
import logging
import pandas as pd

logger = logging.getLogger(__name__)


class BaseTransformer(ABC):
    """Abstract base class for all transformers."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.last_output = None
    
    @abstractmethod
    def transform(self, data: Any) -> pd.DataFrame:
        """Transform data. Must be implemented by subclasses."""
        pass
    
    def run(self, data: Any) -> pd.DataFrame:
        """Execute transformation with logging."""
        logger.info(f"Starting transformation: {self.__class__.__name__}")
        
        input_shape = data.shape if hasattr(data, 'shape') else 'N/A'
        result = self.transform(data)
        output_shape = result.shape if hasattr(result, 'shape') else 'N/A'
        
        self.last_output = result
        
        logger.info(f"Transformation complete: {input_shape} -> {output_shape}")
        return result
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get transformation metadata."""
        return {
            'transformer': self.__class__.__name__,
            'output_shape': self.last_output.shape if self.last_output is not None else None,
        }
