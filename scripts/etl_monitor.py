"""
ETL Monitor — checks data freshness and triggers updates/retrains when needed.
Runs as a long-lived process in the Docker ETL container.

This is the MAIN background process that keeps the pipeline healthy.

Features:
- Checks data freshness every 30 minutes
- Triggers MT5 data fetch when stale (via orchestrator)
- Triggers model retrain when accuracy drops
- Updates pipeline health status
- Sends email alerts on consecutive failures
"""
import time
import logging
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from etl.orchestrator import PipelineOrchestrator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Check every 30 minutes
CHECK_INTERVAL = 1800  # 30 minutes in seconds

# Retrain check: every 6 hours
RETRAIN_CHECK_INTERVAL = 21600  # 6 hours in seconds


def main():
    """Main monitoring loop."""
    orch = PipelineOrchestrator()
    
    logger.info("=" * 70)
    logger.info("ETL MONITOR STARTED")
    logger.info("=" * 70)
    logger.info(f"  Check interval: {CHECK_INTERVAL}s ({CHECK_INTERVAL // 60} minutes)")
    logger.info(f"  Retrain check: every {RETRAIN_CHECK_INTERVAL // 3600} hours")
    logger.info(f"  Freshness threshold: {orch.freshness.max_age_hours} hours")
    logger.info("=" * 70)
    
    last_retrain_check = 0
    check_count = 0
    
    while True:
        try:
            check_count += 1
            now = time.time()
            
            logger.info(f"--- Check #{check_count} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
            
            # 1. Check data freshness for all assets
            stale_assets = []
            for asset in ['gold', 'silver']:
                fresh = orch.freshness.check(asset)
                if fresh['is_fresh']:
                    logger.info(f"  {asset.upper()}: FRESH ({fresh['age_hours']}h old, {fresh['rows']} rows)")
                else:
                    logger.warning(f"  {asset.upper()}: STALE ({fresh['age_hours']}h old, max: {orch.freshness.max_age_hours}h)")
                    stale_assets.append(asset)
            
            # 2. Trigger update for stale assets
            if stale_assets:
                logger.info(f"  Triggering update for stale assets: {stale_assets}")
                for asset in stale_assets:
                    try:
                        result = orch.run_update(asset)
                        if result['success']:
                            logger.info(f"  ✓ {asset.upper()} update successful: {result['freshness']['message']}")
                        else:
                            logger.error(f"  ✗ {asset.upper()} update failed: {result['error']}")
                    except Exception as e:
                        logger.error(f"  ✗ {asset.upper()} update exception: {e}")
            
            # 3. Periodic retrain check (every 6 hours)
            if now - last_retrain_check >= RETRAIN_CHECK_INTERVAL:
                last_retrain_check = now
                logger.info("  Checking retrain conditions...")
                
                for asset in ['gold', 'silver']:
                    try:
                        # Import here to avoid circular imports
                        from self_learning.tracker import OutcomeTracker
                        from self_learning.retrainer import ModelRetrainer
                        
                        tracker = OutcomeTracker()
                        retrainer = ModelRetrainer()
                        
                        summary = tracker.get_summary(days=7)
                        should_retrain = retrainer.should_retrain(
                            min_outcomes=50, 
                            accuracy_threshold=0.55
                        )
                        
                        logger.info(f"  {asset.upper()} retrain check: "
                                  f"outcomes={summary['total']}, "
                                  f"win_rate={summary['win_rate']:.1%}, "
                                  f"should_retrain={should_retrain}")
                        
                        if should_retrain:
                            logger.info(f"  Triggering retrain for {asset.upper()}...")
                            result = orch.run_retrain(asset, trials=20)
                            if result['success']:
                                logger.info(f"  ✓ {asset.upper()} retrain successful: accuracy={result['accuracy']:.2%}")
                            else:
                                logger.error(f"  ✗ {asset.upper()} retrain failed: {result['error']}")
                    
                    except Exception as e:
                        logger.error(f"  Retrain check failed for {asset}: {e}")
            
            # 4. Log health status summary
            health = orch.health.get_status()
            logger.info(f"  Health: failures={health['consecutive_failures']}, "
                       f"last_update={health.get('last_update', 'never')}, "
                       f"last_retrain={health.get('last_retrain', 'never')}")
            
        except Exception as e:
            logger.error(f"Monitor error: {e}")
            import traceback
            traceback.print_exc()
        
        logger.info(f"  Next check in {CHECK_INTERVAL // 60} minutes")
        logger.info("")
        time.sleep(CHECK_INTERVAL)


if __name__ == '__main__':
    main()
