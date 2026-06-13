"""Main ETL Pipeline Orchestrator."""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from .extractors.base import BaseExtractor
from .transformers.base import BaseTransformer
from .loaders.base import BaseLoader
from .exceptions import PipelineError

logger = logging.getLogger(__name__)


class PipelineStatus(Enum):
    """Pipeline execution status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"  # Some stages succeeded, some failed


@dataclass
class PipelineResult:
    """Result of pipeline execution."""
    status: PipelineStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    records_processed: int = 0
    error: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    stage_results: Dict[str, Any] = field(default_factory=dict)


class ETLPipeline:
    """Main ETL Pipeline Orchestrator."""
    
    def __init__(
        self,
        name: str,
        extractor: BaseExtractor,
        transformers: List[BaseTransformer],
        loaders: List[BaseLoader],
        config: Dict[str, Any] = None
    ):
        """
        Initialize ETL Pipeline.
        
        Args:
            name: Pipeline name
            extractor: Data extractor instance
            transformers: List of transformer instances
            loaders: List of loader instances
            config: Optional configuration dictionary
        """
        self.name = name
        self.extractor = extractor
        self.transformers = transformers
        self.loaders = loaders
        self.config = config or {}
        self.last_result: Optional[PipelineResult] = None
        self.run_count = 0
    
    def run(self) -> PipelineResult:
        """Execute the complete ETL pipeline."""
        self.run_count += 1
        
        result = PipelineResult(
            status=PipelineStatus.RUNNING,
            started_at=datetime.now()
        )
        
        logger.info("=" * 80)
        logger.info(f"Starting ETL Pipeline: {self.name} (Run #{self.run_count})")
        logger.info("=" * 80)
        
        data = None
        
        try:
            # ========== EXTRACT ==========
            logger.info("PHASE 1: EXTRACT")
            logger.info("-" * 80)
            
            data = self.extractor.run()
            
            result.metrics['extracted_rows'] = len(data)
            result.stage_results['extract'] = {
                'success': True,
                'rows': len(data),
                'metadata': self.extractor.get_metadata()
            }
            
            logger.info(f"✓ Extraction complete: {len(data)} records")
            logger.info("")
            
            # ========== TRANSFORM ==========
            logger.info("PHASE 2: TRANSFORM")
            logger.info("-" * 80)
            
            for i, transformer in enumerate(self.transformers, 1):
                logger.info(f"Step {i}/{len(self.transformers)}: {transformer.__class__.__name__}")
                
                input_rows = len(data)
                data = transformer.run(data)
                output_rows = len(data)
                
                result.stage_results[f'transform_{i}'] = {
                    'success': True,
                    'transformer': transformer.__class__.__name__,
                    'input_rows': input_rows,
                    'output_rows': output_rows,
                    'metadata': transformer.get_metadata()
                }
                
                logger.info(f"  Input: {input_rows} rows → Output: {output_rows} rows")
            
            result.metrics['transformed_rows'] = len(data)
            result.metrics['feature_count'] = len(data.columns)
            
            logger.info(f"✓ Transformation complete: {len(data)} records, {len(data.columns)} features")
            logger.info("")
            
            # ========== LOAD ==========
            logger.info("PHASE 3: LOAD")
            logger.info("-" * 80)
            
            for i, loader in enumerate(self.loaders, 1):
                logger.info(f"Loader {i}/{len(self.loaders)}: {loader.__class__.__name__}")
                
                success = loader.run(data)
                
                if not success:
                    raise PipelineError(f"Loader failed: {loader.__class__.__name__}")
                
                result.stage_results[f'load_{i}'] = {
                    'success': True,
                    'loader': loader.__class__.__name__,
                    'metadata': loader.get_metadata()
                }
                
                logger.info(f"  ✓ Loaded {loader.records_loaded} records")
            
            result.metrics['loaded_rows'] = len(data)
            
            logger.info(f"✓ Load complete: {len(data)} records")
            logger.info("")
            
            # ========== SUCCESS ==========
            result.status = PipelineStatus.SUCCESS
            result.records_processed = len(data)
            result.completed_at = datetime.now()
            
            duration = (result.completed_at - result.started_at).total_seconds()
            
            logger.info("=" * 80)
            logger.info(f"✓ Pipeline '{self.name}' completed successfully")
            logger.info(f"  Duration: {duration:.2f}s")
            logger.info(f"  Records processed: {result.records_processed}")
            logger.info(f"  Features generated: {result.metrics.get('feature_count', 'N/A')}")
            logger.info("=" * 80)
            logger.info("")
            
        except Exception as e:
            result.status = PipelineStatus.FAILED
            result.error = str(e)
            result.completed_at = datetime.now()
            
            duration = (result.completed_at - result.started_at).total_seconds()
            
            logger.error("=" * 80)
            logger.error(f"✗ Pipeline '{self.name}' failed after {duration:.2f}s")
            logger.error(f"  Error: {str(e)}")
            logger.error("=" * 80)
            logger.error("")
            
            # Don't re-raise, just return failed result
            # This allows scheduler to continue
        
        finally:
            self.last_result = result
        
        return result
    
    def get_status(self) -> Dict[str, Any]:
        """Get current pipeline status."""
        if self.last_result is None:
            return {
                'name': self.name,
                'status': 'never_run',
                'run_count': self.run_count,
                'last_run': None,
                'records': 0
            }
        
        return {
            'name': self.name,
            'status': self.last_result.status.value,
            'run_count': self.run_count,
            'last_run': self.last_result.started_at.isoformat(),
            'duration': (
                (self.last_result.completed_at - self.last_result.started_at).total_seconds()
                if self.last_result.completed_at else None
            ),
            'records': self.last_result.records_processed,
            'error': self.last_result.error
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get detailed pipeline metrics."""
        if self.last_result is None:
            return {}
        
        return {
            'name': self.name,
            'status': self.last_result.status.value,
            'metrics': self.last_result.metrics,
            'stage_results': self.last_result.stage_results
        }
