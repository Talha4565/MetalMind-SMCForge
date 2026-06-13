#!/usr/bin/env python
"""ETL Pipeline Entry Point."""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

from etl.config import ETLConfig
from etl.factory import PipelineFactory
from etl.scheduler import ETLScheduler

# Setup logging
def setup_logging(config: ETLConfig):
    """Configure logging."""
    log_dir = Path(config.log_dir)
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f'etl_{datetime.now():%Y%m%d}.log'
    
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file)
        ]
    )

logger = logging.getLogger(__name__)


def run_once(asset: str, config: ETLConfig):
    """Run pipeline once for specified asset."""
    logger.info(f"Running {asset.upper()} pipeline once...")
    
    if asset.lower() == 'gold':
        pipeline = PipelineFactory.create_gold_pipeline(config)
    elif asset.lower() == 'silver':
        pipeline = PipelineFactory.create_silver_pipeline(config)
    else:
        logger.error(f"Unknown asset: {asset}")
        return None
    
    result = pipeline.run()
    
    print("\n" + "=" * 80)
    print(f"Pipeline Status: {result.status.value.upper()}")
    print("=" * 80)
    print(f"Records processed: {result.records_processed}")
    print(f"Duration: {(result.completed_at - result.started_at).total_seconds():.2f}s")
    if result.error:
        print(f"Error: {result.error}")
    print("=" * 80)
    
    return result


def run_scheduled(config: ETLConfig, interval_minutes: int = None):
    """Run pipelines on schedule."""
    interval = interval_minutes or config.schedule_interval_minutes
    
    logger.info(f"Starting scheduled ETL pipelines (interval: {interval} minutes)...")
    
    scheduler = ETLScheduler()
    
    # Create pipelines
    gold_pipeline = PipelineFactory.create_gold_pipeline(config)
    silver_pipeline = PipelineFactory.create_silver_pipeline(config)
    
    # Add to scheduler
    scheduler.add_pipeline(gold_pipeline, interval_minutes=interval, run_immediately=True)
    scheduler.add_pipeline(silver_pipeline, interval_minutes=interval, run_immediately=True)
    
    # Start scheduler
    scheduler.start()
    
    print("\n" + "=" * 80)
    print("ETL Scheduler running")
    print(f"Interval: Every {interval} minutes")
    print("Pipelines:")
    print("  - Gold ETL Pipeline")
    print("  - Silver ETL Pipeline")
    print("\nPress Ctrl+C to stop.")
    print("=" * 80 + "\n")
    
    try:
        # Keep running
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nStopping scheduler...")
        scheduler.stop()
        print("Scheduler stopped. Goodbye!")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='ETL Pipeline Runner for ML Trading Signals',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run gold pipeline once
  python run_etl.py run --asset gold
  
  # Run all pipelines once
  python run_etl.py run --asset all
  
  # Run on schedule (every 15 minutes)
  python run_etl.py schedule
  
  # Run on custom schedule (every 30 minutes)
  python run_etl.py schedule --interval 30
        """
    )
    
    parser.add_argument(
        'command',
        choices=['run', 'schedule', 'status'],
        help='Command to execute'
    )
    
    parser.add_argument(
        '--asset',
        choices=['gold', 'silver', 'all'],
        default='all',
        help='Asset to process (for run command)'
    )
    
    parser.add_argument(
        '--interval',
        type=int,
        default=None,
        help='Schedule interval in minutes (for schedule command)'
    )
    
    parser.add_argument(
        '--config',
        default=None,
        help='Path to config file (not implemented yet)'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = ETLConfig.from_env()
    config.log_level = args.log_level
    
    # Setup logging
    setup_logging(config)
    
    # Validate configuration
    if not config.validate():
        logger.error("Configuration validation failed")
        sys.exit(1)
    
    # Execute command
    if args.command == 'run':
        if args.asset == 'all':
            logger.info("Running all pipelines...")
            run_once('gold', config)
            run_once('silver', config)
        else:
            run_once(args.asset, config)
    
    elif args.command == 'schedule':
        run_scheduled(config, interval_minutes=args.interval)
    
    elif args.command == 'status':
        # TODO: Implement status check
        print("Status command not yet implemented")


if __name__ == '__main__':
    main()
