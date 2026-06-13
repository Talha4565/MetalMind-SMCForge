#!/usr/bin/env python
"""ETL Pipeline Demo Version - Fast execution with 10K rows."""

import logging
import sys
from datetime import datetime
from pathlib import Path

from etl.extractors.csv_extractor import CSVExtractor
from etl.transformers.quality_transformer import DataQualityTransformer
from etl.transformers.feature_transformer import FeatureTransformer
from etl.loaders.db_loader import DatabaseLoader
from etl.loaders.feature_store_loader import FeatureStoreLoader
from etl.pipeline import ETLPipeline

# Setup logging
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f'etl_demo_{datetime.now():%Y%m%d_%H%M%S}.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file)
    ]
)

logger = logging.getLogger(__name__)


def create_demo_pipeline(asset: str = 'XAUUSD', max_rows: int = 10000):
    """Create fast demo pipeline with limited rows."""
    
    if asset == 'XAUUSD':
        csv_file = 'Gold Dataset/Gold_15m_Candlestick.csv'
        table_name = 'gold_features_demo'
    else:
        csv_file = 'Silver Dataset/Silver_15m_Candlestick.csv'
        table_name = 'silver_features_demo'
    
    # Extractor with row limit
    extractor = CSVExtractor(
        file_path=csv_file,
        max_rows=max_rows
    )
    
    # Transformers
    transformers = [
        DataQualityTransformer(
            handle_missing='ffill',
            remove_outliers=True,
            outlier_std=5.0
        ),
        FeatureTransformer(
            asset=asset,
            include_labels=True
        )
    ]
    
    # Loaders
    loaders = [
        DatabaseLoader(
            connection_string='sqlite:///instance/metalmind_smc.db',
            table_name=table_name,
            if_exists='replace'
        ),
        FeatureStoreLoader(
            store_path='data/features',
            asset=asset,
            version=True,
            format='parquet'
        )
    ]
    
    return ETLPipeline(
        name=f'{asset} Demo Pipeline',
        extractor=extractor,
        transformers=transformers,
        loaders=loaders
    )


def main():
    """Run demo pipeline."""
    print("\n" + "=" * 80)
    print("ETL PIPELINE DEMO - Fast Execution (10,000 rows)")
    print("=" * 80 + "\n")
    
    # Run Gold pipeline
    print("Running GOLD pipeline...")
    gold_pipeline = create_demo_pipeline('XAUUSD', max_rows=10000)
    result = gold_pipeline.run()
    
    if result.status.value == 'success':
        print("\n" + "=" * 80)
        print("✓ GOLD PIPELINE SUCCESS")
        print("=" * 80)
        print(f"Records: {result.records_processed}")
        print(f"Features: {result.metrics.get('feature_count', 'N/A')}")
        print(f"Duration: {(result.completed_at - result.started_at).total_seconds():.2f}s")
        print("=" * 80 + "\n")
    else:
        print("\n" + "=" * 80)
        print("✗ GOLD PIPELINE FAILED")
        print("=" * 80)
        print(f"Error: {result.error}")
        print("=" * 80 + "\n")
        return
    
    # Run Silver pipeline
    print("Running SILVER pipeline...")
    silver_pipeline = create_demo_pipeline('XAGUSD', max_rows=10000)
    result = silver_pipeline.run()
    
    if result.status.value == 'success':
        print("\n" + "=" * 80)
        print("✓ SILVER PIPELINE SUCCESS")
        print("=" * 80)
        print(f"Records: {result.records_processed}")
        print(f"Features: {result.metrics.get('feature_count', 'N/A')}")
        print(f"Duration: {(result.completed_at - result.started_at).total_seconds():.2f}s")
        print("=" * 80 + "\n")
    else:
        print("\n" + "=" * 80)
        print("✗ SILVER PIPELINE FAILED")
        print("=" * 80)
        print(f"Error: {result.error}")
        print("=" * 80 + "\n")
    
    print("\n" + "=" * 80)
    print("DEMO COMPLETE - Check outputs:")
    print("  - Database: instance/metalmind_smc.db")
    print("  - Features: data/features/")
    print("  - Logs: logs/")
    print("=" * 80 + "\n")


if __name__ == '__main__':
    main()
