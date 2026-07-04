"""
Automated pipeline: Fetch live data via MT5 + Append to CSVs + Retrain model.

Usage:
    python run_pipeline.py --mode update            # Fetch latest candles via MT5
    python run_pipeline.py --mode retrain           # Retrain model on full data
    python run_pipeline.py --mode full              # Update + Retrain
    python run_pipeline.py --mode schedule          # Run continuously (15min update + 24h retrain)
    python run_pipeline.py --mode status            # Show pipeline status
    python run_pipeline.py --mode freshness         # Check data freshness
    python run_pipeline.py --mode backups           # List model backups

Requires MetaTrader 5 terminal running on the host machine.
"""

import sys
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from etl.orchestrator import PipelineOrchestrator
from config.settings import GOLD_DATASET_DIR, SILVER_DATASET_DIR, REPORTS_DIR

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global orchestrator instance
orchestrator = PipelineOrchestrator()


def run_fetch_and_append(asset: str, intervals: list = None):
    """Fetch live data and append to CSVs using MT5.
    
    Requires MetaTrader 5 terminal running on the host.
    """
    if intervals is None:
        intervals = ['5m', '15m', '30m', '1h']
    
    logger.info("=" * 60)
    logger.info(f"FETCH & APPEND: {asset.upper()}")
    logger.info("=" * 60)
    
    try:
        import MetaTrader5 as mt5
        if mt5.initialize():
            logger.info("MT5 available, using MT5 for data fetch")
            mt5.shutdown()
            import subprocess
            result = subprocess.run(
                [sys.executable, 'scripts/mt5_update.py', '--asset', asset],
                capture_output=True, text=True, cwd=str(Path(__file__).parent)
            )
            if result.returncode == 0:
                logger.info(f"✓ {asset.upper()} data updated via MT5")
                return
            else:
                logger.error(f"MT5 update failed: {result.stderr}")
        else:
            logger.error(f"MT5 initialize failed: {mt5.last_error()}")
    except ImportError:
        logger.error("MetaTrader5 not installed. Run: pip install MetaTrader5")
    except Exception as e:
        logger.error(f"MT5 error: {e}")


def run_backfill(asset: str):
    """Backfill historical gap from Sept 2024 to today."""
    logger.info(f"=" * 60)
    logger.info(f"BACKFILL: {asset.upper()}")
    logger.info(f"=" * 60)
    
    # Fetch all available intervals
    # 1h covers 730 days (Sept 2024 → today)
    # 15m/30m/5m cover last 60 days
    intervals = ['5m', '15m', '30m', '1h']
    
    run_fetch_and_append(asset, intervals)
    
    logger.info(f"✓ Backfill complete for {asset}")


def run_retrain(asset: str, trials: int = 30):
    """Retrain model on full dataset."""
    logger.info(f"=" * 60)
    logger.info(f"RETRAIN: {asset.upper()}")
    logger.info(f"=" * 60)
    
    from models.retrain import retrain_model
    result = retrain_model(asset, trials)
    
    return result


def run_full_pipeline(asset: str):
    """Run full pipeline: backfill → retrain."""
    logger.info(f"=" * 60)
    logger.info(f"FULL PIPELINE: {asset.upper()}")
    logger.info(f"=" * 60)
    
    # Step 1: Backfill
    run_backfill(asset)
    
    # Step 2: Retrain
    result = run_retrain(asset)
    
    logger.info(f"✓ Full pipeline complete for {asset}")
    return result


def run_schedule():
    """Run continuous scheduler: 15min updates + 24h retrain."""
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    from apscheduler.triggers.cron import CronTrigger
    
    scheduler = BlockingScheduler()
    
    # Update data every 15 minutes
    for asset in ['gold', 'silver']:
        scheduler.add_job(
            func=run_fetch_and_append,
            trigger=IntervalTrigger(minutes=15),
            args=[asset, ['5m', '15m', '30m', '1h']],
            id=f'{asset}_update',
            name=f'{asset} data update',
            replace_existing=True
        )
        logger.info(f"Scheduled {asset} update every 15 minutes")
    
    # Retrain every 24 hours at 3 AM UTC
    for asset in ['gold', 'silver']:
        scheduler.add_job(
            func=run_retrain,
            trigger=CronTrigger(hour=3, minute=0),
            args=[asset],
            id=f'{asset}_retrain',
            name=f'{asset} model retrain',
            replace_existing=True
        )
        logger.info(f"Scheduled {asset} retrain daily at 03:00 UTC")
    
    logger.info("=" * 60)
    logger.info("Pipeline scheduler started")
    logger.info("  Updates: every 15 minutes")
    logger.info("  Retrains: daily at 03:00 UTC")
    logger.info("=" * 60)
    
    # Run first update immediately
    for asset in ['gold', 'silver']:
        run_fetch_and_append(asset)
    
    scheduler.start()


def main():
    parser = argparse.ArgumentParser(description='ML-Signals Automated Pipeline')
    parser.add_argument('--mode', choices=['backfill', 'update', 'retrain', 'full', 'schedule', 'status', 'freshness', 'backups'],
                       default='update', help='Pipeline mode')
    parser.add_argument('--asset', choices=['gold', 'silver'], default='gold',
                       help='Asset to process')
    parser.add_argument('--trials', type=int, default=30,
                       help='Optuna trials for retraining')
    args = parser.parse_args()
    
    if args.mode == 'backfill':
        run_backfill(args.asset)
    elif args.mode == 'update':
        run_fetch_and_append(args.asset)
    elif args.mode == 'retrain':
        run_retrain(args.asset, args.trials)
    elif args.mode == 'full':
        run_full_pipeline(args.asset)
    elif args.mode == 'schedule':
        run_schedule()
    elif args.mode == 'status':
        print(json.dumps(orchestrator.get_dashboard_data(), indent=2, default=str))
    elif args.mode == 'freshness':
        for asset in ['gold', 'silver']:
            result = orchestrator.freshness.check(asset)
            status = "FRESH" if result['is_fresh'] else "STALE"
            print(f"{asset.upper()}: {status} - {result['message']} (rows: {result['rows']})")
    elif args.mode == 'backups':
        backups = orchestrator.versioning.list_backups()
        if backups:
            for b in backups:
                print(f"  {b['name']} ({b['size_mb']} MB)")
        else:
            print("No backups found")


if __name__ == '__main__':
    main()
