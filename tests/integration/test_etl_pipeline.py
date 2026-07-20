"""Integration tests for the ETL pipeline."""
import sys
from pathlib import Path
import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class MockExtractor:
    """Mock extractor for testing."""

    def __init__(self, data=None):
        self._data = data if data is not None else pd.DataFrame({
            'open': [1, 2, 3],
            'high': [2, 3, 4],
            'low': [0, 1, 2],
            'close': [1.5, 2.5, 3.5],
            'volume': [100, 200, 300]
        })
        self.last_run = None
        self.records_extracted = 0

    def extract(self):
        return self._data

    def validate(self, data):
        return isinstance(data, pd.DataFrame) and len(data) > 0

    def run(self):
        data = self.extract()
        if not self.validate(data):
            raise ValueError("Data validation failed")
        self.last_run = datetime.now()
        self.records_extracted = len(data)
        return data

    def get_metadata(self):
        return {
            'extractor': 'MockExtractor',
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'records_extracted': self.records_extracted,
        }


class MockTransformer:
    """Mock transformer that adds a column."""

    def __init__(self, col_name='transformed'):
        self.col_name = col_name
        self.last_run = None

    def transform(self, data):
        data = data.copy()
        data[self.col_name] = data['close'] * 2
        return data

    def run(self, data):
        result = self.transform(data)
        self.last_run = datetime.now()
        return result

    def get_metadata(self):
        return {'transformer': 'MockTransformer', 'last_run': self.last_run.isoformat() if self.last_run else None}


class MockFailingTransformer:
    """Transformer that raises an error."""

    def transform(self, data):
        raise ValueError("Transform failed intentionally")


class MockLoader:
    """Mock loader that records loaded data."""

    def __init__(self):
        self.loaded_data = None
        self.records_loaded = 0
        self.last_run = None

    def load(self, data):
        self.loaded_data = data
        self.records_loaded = len(data) if hasattr(data, '__len__') else 0
        return True

    def run(self, data):
        success = self.load(data)
        self.last_run = datetime.now()
        return success

    def get_metadata(self):
        return {'loader': 'MockLoader', 'last_run': self.last_run.isoformat() if self.last_run else None}


class MockFailingLoader:
    """Loader that returns False."""

    def load(self, data):
        return False


class TestETLPipelineIntegration:
    """Test full ETL pipeline flow."""

    def _permissive_gate(self):
        """Return a DataQualityGate that won't block small mock datasets."""
        from etl.guards.data_quality_gate import DataQualityGate
        return DataQualityGate(config={"min_rows_required": 0, "max_price_change_pct": 999})

    def test_successful_pipeline(self, etl_pipeline):
        ETLPipeline, PipelineResult, PipelineStatus = etl_pipeline
        extractor = MockExtractor()
        transformers = [MockTransformer('col_a'), MockTransformer('col_b')]
        loaders = [MockLoader()]

        pipeline = ETLPipeline(
            name='Test Pipeline',
            extractor=extractor,
            transformers=transformers,
            loaders=loaders,
            data_quality_gate=self._permissive_gate(),
        )

        result = pipeline.run()
        assert result.status == PipelineStatus.SUCCESS
        assert result.records_processed == 3
        assert result.stage_results['transform_1']['success'] is True

    def test_pipeline_failed_transformer(self, etl_pipeline):
        ETLPipeline, PipelineResult, PipelineStatus = etl_pipeline
        extractor = MockExtractor()
        transformers = [MockFailingTransformer()]
        loaders = [MockLoader()]

        pipeline = ETLPipeline(
            name='Failing Pipeline',
            extractor=extractor,
            transformers=transformers,
            loaders=loaders,
            data_quality_gate=self._permissive_gate(),
        )

        result = pipeline.run()
        assert result.status == PipelineStatus.FAILED
        assert result.error is not None

    def test_pipeline_failed_loader(self, etl_pipeline):
        ETLPipeline, PipelineResult, PipelineStatus = etl_pipeline
        extractor = MockExtractor()
        transformers = [MockTransformer()]
        loaders = [MockFailingLoader()]

        pipeline = ETLPipeline(
            name='Failing Load Pipeline',
            extractor=extractor,
            transformers=transformers,
            loaders=loaders,
            data_quality_gate=self._permissive_gate(),
        )

        result = pipeline.run()
        assert result.status == PipelineStatus.FAILED

    def test_pipeline_status_tracking(self, etl_pipeline):
        ETLPipeline, PipelineResult, PipelineStatus = etl_pipeline
        extractor = MockExtractor()
        pipeline = ETLPipeline(
            name='Status Pipeline',
            extractor=extractor,
            transformers=[],
            loaders=[MockLoader()],
            data_quality_gate=self._permissive_gate(),
        )

        status = pipeline.get_status()
        assert status['status'] == 'never_run'
        assert status['run_count'] == 0

        pipeline.run()
        status = pipeline.get_status()
        assert status['status'] == 'success'
        assert status['run_count'] == 1

    def test_pipeline_metrics(self, etl_pipeline):
        ETLPipeline, PipelineResult, PipelineStatus = etl_pipeline
        extractor = MockExtractor()
        pipeline = ETLPipeline(
            name='Metrics Pipeline',
            extractor=extractor,
            transformers=[MockTransformer()],
            loaders=[MockLoader()],
            data_quality_gate=self._permissive_gate(),
        )

        pipeline.run()
        metrics = pipeline.get_metrics()
        assert 'extracted_rows' in metrics['metrics']
        assert 'transformed_rows' in metrics['metrics']

    def test_pipeline_run_count_increments(self, etl_pipeline):
        ETLPipeline, PipelineResult, PipelineStatus = etl_pipeline
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

    def test_pipeline_result_has_timestamps(self, etl_pipeline):
        ETLPipeline, PipelineResult, PipelineStatus = etl_pipeline
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

    def test_pipeline_skipped_by_data_quality_gate(self, etl_pipeline):
        """When the gate says should_continue=False, the run returns SKIPPED early."""
        ETLPipeline, PipelineResult, PipelineStatus = etl_pipeline
        from etl.guards.data_quality_gate import ValidationResult

        class BlockingGate:
            def validate(self, df, asset="gold"):
                return ValidationResult(
                    passed=False, rows_before=len(df), rows_after=5,
                    issues=["too few rows"], should_continue=False, cleaned_df=df,
                )

        extractor = MockExtractor()
        pipeline = ETLPipeline(
            name="Skipped Pipeline",
            extractor=extractor,
            transformers=[MockTransformer()],
            loaders=[MockLoader()],
            data_quality_gate=BlockingGate(),
        )
        result = pipeline.run()
        assert result.status == PipelineStatus.SKIPPED
        assert "transform_1" not in result.stage_results
        assert "data_quality_gate" in result.stage_results
