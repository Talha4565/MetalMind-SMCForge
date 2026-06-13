"""Factory for creating pre-configured ETL pipelines."""

from typing import Dict, Any
from .pipeline import ETLPipeline
from .extractors.csv_extractor import CSVExtractor
from .extractors.api_extractor import APIExtractor
from .transformers.quality_transformer import DataQualityTransformer
from .transformers.feature_transformer import FeatureTransformer
from .loaders.db_loader import DatabaseLoader
from .loaders.feature_store_loader import FeatureStoreLoader
from .config import ETLConfig
import logging

logger = logging.getLogger(__name__)


class PipelineFactory:
    """Factory for creating pre-configured pipelines."""
    
    @staticmethod
    def create_gold_pipeline(config: ETLConfig) -> ETLPipeline:
        """
        Create pipeline for Gold (XAUUSD) data.
        
        Flow: CSV → Quality Check → Feature Engineering → Database + Feature Store
        """
        logger.info("Creating Gold ETL pipeline...")
        
        # Extractor: CSV file
        extractor = CSVExtractor(
            file_path=config.gold_data_path,
            date_column='timestamp',
            required_columns=['open', 'high', 'low', 'close', 'volume']
        )
        
        # Transformers: Quality + Features
        transformers = [
            DataQualityTransformer(
                handle_missing=config.handle_missing,
                remove_outliers=config.remove_outliers,
                outlier_std=config.outlier_std
            ),
            FeatureTransformer(
                asset='XAUUSD',
                include_labels=config.include_labels,
                label_config={
                    'threshold': config.label_threshold,
                    'lookahead': config.label_lookahead
                }
            )
        ]
        
        # Loaders: Database + Feature Store
        loaders = [
            DatabaseLoader(
                connection_string=config.database_url,
                table_name='gold_features',
                if_exists='replace'
            ),
            FeatureStoreLoader(
                store_path=config.feature_store_path,
                asset='XAUUSD',
                version=True,
                format='parquet'
            )
        ]
        
        return ETLPipeline(
            name='Gold ETL Pipeline',
            extractor=extractor,
            transformers=transformers,
            loaders=loaders,
            config=config.__dict__
        )
    
    @staticmethod
    def create_silver_pipeline(config: ETLConfig) -> ETLPipeline:
        """
        Create pipeline for Silver (XAGUSD) data.
        
        Flow: CSV → Quality Check → Feature Engineering → Database + Feature Store
        """
        logger.info("Creating Silver ETL pipeline...")
        
        # Extractor: CSV file
        extractor = CSVExtractor(
            file_path=config.silver_data_path,
            date_column='timestamp',
            required_columns=['open', 'high', 'low', 'close', 'volume']
        )
        
        # Transformers: Quality + Features
        transformers = [
            DataQualityTransformer(
                handle_missing=config.handle_missing,
                remove_outliers=config.remove_outliers,
                outlier_std=config.outlier_std
            ),
            FeatureTransformer(
                asset='XAGUSD',
                include_labels=config.include_labels,
                label_config={
                    'threshold': config.label_threshold,
                    'lookahead': config.label_lookahead
                }
            )
        ]
        
        # Loaders: Database + Feature Store
        loaders = [
            DatabaseLoader(
                connection_string=config.database_url,
                table_name='silver_features',
                if_exists='replace'
            ),
            FeatureStoreLoader(
                store_path=config.feature_store_path,
                asset='XAGUSD',
                version=True,
                format='parquet'
            )
        ]
        
        return ETLPipeline(
            name='Silver ETL Pipeline',
            extractor=extractor,
            transformers=transformers,
            loaders=loaders,
            config=config.__dict__
        )
    
    @staticmethod
    def create_api_pipeline(
        asset: str,
        api_url: str,
        api_key: str,
        config: ETLConfig
    ) -> ETLPipeline:
        """
        Create pipeline for real-time API data.
        
        Flow: API → Quality Check → Feature Engineering → Database + Feature Store
        """
        logger.info(f"Creating {asset} API pipeline...")
        
        # Extractor: API
        extractor = APIExtractor(
            base_url=api_url,
            asset=asset,
            api_key=api_key,
            lookback_days=30
        )
        
        # Transformers: Quality + Features
        transformers = [
            DataQualityTransformer(
                handle_missing=config.handle_missing,
                remove_outliers=config.remove_outliers
            ),
            FeatureTransformer(
                asset=asset,
                include_labels=config.include_labels
            )
        ]
        
        # Loaders: Database + Feature Store
        table_name = f"{asset.lower()}_features"
        loaders = [
            DatabaseLoader(
                connection_string=config.database_url,
                table_name=table_name,
                if_exists='append'  # Append for real-time data
            ),
            FeatureStoreLoader(
                store_path=config.feature_store_path,
                asset=asset,
                version=True
            )
        ]
        
        return ETLPipeline(
            name=f'{asset} API Pipeline',
            extractor=extractor,
            transformers=transformers,
            loaders=loaders
        )
