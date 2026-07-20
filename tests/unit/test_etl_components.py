"""Unit tests for ETL pipeline components."""
import sys
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestETLExceptions:
    """Test custom exception hierarchy."""

    def test_base_exception(self, etl_config_and_exceptions):
        ETLException = etl_config_and_exceptions["ETLException"]
        with pytest.raises(ETLException):
            raise ETLException("test")

    def test_extraction_error_is_etl(self, etl_config_and_exceptions):
        ETLException = etl_config_and_exceptions["ETLException"]
        ExtractionError = etl_config_and_exceptions["ExtractionError"]
        with pytest.raises(ETLException):
            raise ExtractionError("test")

    def test_transformation_error_is_etl(self, etl_config_and_exceptions):
        ETLException = etl_config_and_exceptions["ETLException"]
        TransformationError = etl_config_and_exceptions["TransformationError"]
        with pytest.raises(ETLException):
            raise TransformationError("test")

    def test_load_error_is_etl(self, etl_config_and_exceptions):
        ETLException = etl_config_and_exceptions["ETLException"]
        LoadError = etl_config_and_exceptions["LoadError"]
        with pytest.raises(ETLException):
            raise LoadError("test")

    def test_validation_error_is_etl(self, etl_config_and_exceptions):
        ETLException = etl_config_and_exceptions["ETLException"]
        ValidationError = etl_config_and_exceptions["ValidationError"]
        with pytest.raises(ETLException):
            raise ValidationError("test")

    def test_configuration_error_is_etl(self, etl_config_and_exceptions):
        ETLException = etl_config_and_exceptions["ETLException"]
        ConfigurationError = etl_config_and_exceptions["ConfigurationError"]
        with pytest.raises(ETLException):
            raise ConfigurationError("test")

    def test_pipeline_error_is_etl(self, etl_config_and_exceptions):
        ETLException = etl_config_and_exceptions["ETLException"]
        PipelineError = etl_config_and_exceptions["PipelineError"]
        with pytest.raises(ETLException):
            raise PipelineError("test")


class TestETLConfig:
    """Test ETL configuration."""

    def test_default_config(self, etl_config_and_exceptions):
        ETLConfig = etl_config_and_exceptions["ETLConfig"]
        config = ETLConfig()
        assert config.gold_data_path is not None
        assert config.silver_data_path is not None
        assert config.schedule_interval_minutes == 15
        assert config.batch_size == 1000
        assert config.max_retries == 3

    def test_config_from_env(self, etl_config_and_exceptions):
        import os
        ETLConfig = etl_config_and_exceptions["ETLConfig"]
        os.environ['GOLD_DATA_PATH'] = 'test_gold.csv'
        os.environ['SILVER_DATA_PATH'] = 'test_silver.csv'
        config = ETLConfig.from_env()
        assert config.gold_data_path == 'test_gold.csv'
        assert config.silver_data_path == 'test_silver.csv'
        del os.environ['GOLD_DATA_PATH']
        del os.environ['SILVER_DATA_PATH']

    def test_config_data_quality_defaults(self, etl_config_and_exceptions):
        ETLConfig = etl_config_and_exceptions["ETLConfig"]
        config = ETLConfig()
        assert config.handle_missing == 'ffill'
        assert config.remove_outliers is True
        assert config.outlier_std == 5.0

    def test_config_feature_defaults(self, etl_config_and_exceptions):
        ETLConfig = etl_config_and_exceptions["ETLConfig"]
        config = ETLConfig()
        assert config.include_labels is True
        assert config.label_threshold == 0.002
        assert config.label_lookahead == 12


class TestETLPipeline:
    """Test ETL pipeline orchestration."""

    def test_pipeline_status_enum(self, etl_pipeline):
        ETLPipeline, PipelineResult, PipelineStatus = etl_pipeline
        assert PipelineStatus.PENDING.value == 'pending'
        assert PipelineStatus.RUNNING.value == 'running'
        assert PipelineStatus.SUCCESS.value == 'success'
        assert PipelineStatus.FAILED.value == 'failed'
        assert PipelineStatus.PARTIAL.value == 'partial'

    def test_pipeline_result_dataclass(self, etl_pipeline):
        ETLPipeline, PipelineResult, PipelineStatus = etl_pipeline
        from datetime import datetime
        result = PipelineResult(
            status='running',
            started_at=datetime.now()
        )
        assert result.records_processed == 0
        assert result.error is None
        assert result.metrics == {}
        assert result.stage_results == {}


class TestBaseExtractor:
    """Test base extractor interface."""

    def test_cannot_instantiate_abstract(self, etl_base_classes):
        BaseExtractor, BaseTransformer, BaseLoader = etl_base_classes
        with pytest.raises(TypeError):
            BaseExtractor()


class TestBaseTransformer:
    """Test base transformer interface."""

    def test_cannot_instantiate_abstract(self, etl_base_classes):
        BaseExtractor, BaseTransformer, BaseLoader = etl_base_classes
        with pytest.raises(TypeError):
            BaseTransformer()


class TestBaseLoader:
    """Test base loader interface."""

    def test_cannot_instantiate_abstract(self, etl_base_classes):
        BaseExtractor, BaseTransformer, BaseLoader = etl_base_classes
        with pytest.raises(TypeError):
            BaseLoader()
