"""
Automated pipeline: Fetch live MT5 data → Append to CSVs → Retrain model.

Usage:
    python run_pipeline.py --mode update            # Fetch latest MT5 candles only
    python run_pipeline.py --mode retrain           # Retrain model on full data
    python run_pipeline.py --mode full              # Update + Retrain
    python run_pipeline.py --mode schedule          # Run continuously (15min update + 24h retrain)
    python run_pipeline.py --mode status            # Show pipeline status
    python run_pipeline.py --mode freshness         # Check data freshness
    python run_pipeline.py --mode backups           # List model backups
"""

import sys
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from scripts.mt5_update import update_asset
from etl.orchestrator import PipelineOrchestrator
from config.settings import GOLD_DATASET_DIR, SILVER_DATASET_DIR, REPORTS_DIR

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global orchestrator instance
orchestrator = PipelineOrchestrator()


def run_update(asset: str):
    """Fetch latest MT5 spot data and append to CSVs."""
    logger.info(f"=" * 60)
    logger.info(f"MT5 UPDATE: {asset.upper()}")
    logger.info(f"=" * 60)

    update_asset(asset)
    logger.info(f"✓ {asset.upper()} data updated from MT5")


def run_backfill(asset: str):
    """Backfill using MT5 — fetches latest 500 bars per timeframe."""
    logger.info(f"=" * 60)
    logger.info(f"BACKFILL: {asset.upper()}")
    logger.info(f"=" * 60)

    run_update(asset)
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
    """Run continuous scheduler: 15min MT5 updates + 24h retrain."""
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    from apscheduler.triggers.cron import CronTrigger
    
    scheduler = BlockingScheduler()
    
    # Update data every 15 minutes from MT5
    for asset in ['gold', 'silver']:
        scheduler.add_job(
            func=run_update,
            trigger=IntervalTrigger(minutes=15),
            args=[asset],
            id=f'{asset}_update',
            name=f'{asset} MT5 data update',
            replace_existing=True
        )
        logger.info(f"Scheduled {asset} MT5 update every 15 minutes")
    
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
    logger.info("Pipeline scheduler started (MT5 spot data)")
    logger.info("  Updates: every 15 minutes")
    logger.info("  Retrains: daily at 03:00 UTC")
    logger.info("=" * 60)
    
    # Run first update immediately
    for asset in ['gold', 'silver']:
        run_update(asset)
    
    scheduler.start()


def main():
    parser = argparse.ArgumentParser(description='ML-Signals Automated Pipeline (MT5 Spot Data)')
    parser.add_argument('--mode', choices=['update', 'retrain', 'full', 'schedule', 'status', 'freshness', 'backups'],
                       default='update', help='Pipeline mode')
    parser.add_argument('--asset', choices=['gold', 'silver'], default='gold',
                       help='Asset to process')
    parser.add_argument('--trials', type=int, default=30,
                       help='Optuna trials for retraining')
    args = parser.parse_args()
    
    if args.mode == 'update':
        run_update(args.asset)
    elif args.mode == 'retrain':
        run_retrain(args.asset, args.trials)
    elif args.mode == 'full':
        run_update(args.asset)
        run_retrain(args.asset, args.trials)
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
