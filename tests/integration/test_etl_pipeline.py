"""Integration tests for the ETL pipeline."""
import sys
from pathlib import Path
import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from etl.pipeline import ETLPipeline, PipelineResult, PipelineStatus
from etl.extractors.base import BaseExtractor
from etl.transformers.base import BaseTransformer
from etl.loaders.base import BaseLoader


class MockExtractor(BaseExtractor):
    """Mock extractor for testing."""

    def __init__(self, data=None):
        super().__init__()
        self._data = data if data is not None else pd.DataFrame({
            'open': [1, 2, 3],
            'high': [2, 3, 4],
            'low': [0, 1, 2],
            'close': [1.5, 2.5, 3.5],
            'volume': [100, 200, 300]
        })

    def extract(self):
        return self._data

    def validate(self, data):
        return isinstance(data, pd.DataFrame) and len(data) > 0


class MockTransformer(BaseTransformer):
    """Mock transformer that adds a column."""

    def __init__(self, col_name='transformed'):
        super().__init__()
        self.col_name = col_name

    def transform(self, data):
        data = data.copy()
        data[self.col_name] = data['close'] * 2
        return data


class MockFailingTransformer(BaseTransformer):
    """Transformer that raises an error."""

    def transform(self, data):
        raise ValueError("Transform failed intentionally")


class MockLoader(BaseLoader):
    """Mock loader that records loaded data."""

    def __init__(self):
        super().__init__()
        self.loaded_data = None

    def load(self, data):
        self.loaded_data = data
        return True


class MockFailingLoader(BaseLoader):
    """Loader that returns False."""

    def load(self, data):
        return False


class TestETLPipelineIntegration:
    """Test full ETL pipeline flow."""

    def test_successful_pipeline(self):
        extractor = MockExtractor()
        transformers = [MockTransformer('col_a'), MockTransformer('col_b')]
        loaders = [MockLoader()]

        pipeline = ETLPipeline(
            name='Test Pipeline',
            extractor=extractor,
            transformers=transformers,
            loaders=loaders
        )

        result = pipeline.run()
        assert result.status == PipelineStatus.SUCCESS
        assert result.records_processed == 3
        assert result.stage_results['transform_1']['success'] is True

    def test_pipeline_failed_transformer(self):
        extractor = MockExtractor()
        transformers = [MockFailingTransformer()]
        loaders = [MockLoader()]

        pipeline = ETLPipeline(
            name='Failing Pipeline',
            extractor=extractor,
            transformers=transformers,
            loaders=loaders
        )

        result = pipeline.run()
        assert result.status == PipelineStatus.FAILED
        assert result.error is not None

    def test_pipeline_failed_loader(self):
        extractor = MockExtractor()
        transformers = [MockTransformer()]
        loaders = [MockFailingLoader()]

        pipeline = ETLPipeline(
            name='Failing Load Pipeline',
            extractor=extractor,
            transformers=transformers,
            loaders=loaders
        )

        result = pipeline.run()
        assert result.status == PipelineStatus.FAILED

    def test_pipeline_status_tracking(self):
        extractor = MockExtractor()
        pipeline = ETLPipeline(
            name='Status Pipeline',
            extractor=extractor,
            transformers=[],
            loaders=[MockLoader()]
        )

        status = pipeline.get_status()
        assert status['status'] == 'never_run'
        assert status['run_count'] == 0

        pipeline.run()
        status = pipeline.get_status()
        assert status['status'] == 'success'
        assert status['run_count'] == 1

    def test_pipeline_metrics(self):
        extractor = MockExtractor()
        pipeline = ETLPipeline(
            name='Metrics Pipeline',
            extractor=extractor,
            transformers=[MockTransformer()],
            loaders=[MockLoader()]
        )

        pipeline.run()
        metrics = pipeline.get_metrics()
        assert 'extracted_rows' in metrics['metrics']
        assert 'transformed_rows' in metrics['metrics']

    def test_pipeline_run_count_increments(self):
        extractor = MockExtractor()
        pipeline = ETLPipeline(
            name='Count Pipeline',
            extractor=extractor,
            transformers=[],
            loaders=[MockLoader()]
        )

        pipeline.run()
        pipeline.run()
        assert pipeline.run_count == 2

    def test_pipeline_result_has_timestamps(self):
        extractor = MockExtractor()
        pipeline = ETLPipeline(
            name='Timestamp Pipeline',
            extractor=extractor,
            transformers=[],
            loaders=[MockLoader()]
        )

        result = pipeline.run()
        assert result.started_at is not None
        assert result.completed_at is not None
        assert result.completed_at >= result.started_at
