"""
ETL Monitor — checks data freshness and triggers retrain when needed.
Runs as a long-lived process in the Docker ETL container.
"""
import time
import logging
from etl.orchestrator import PipelineOrchestrator
from self_learning.retrainer import ModelRetrainer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CHECK_INTERVAL = 1800  # 30 minutes


def main():
    orch = PipelineOrchestrator()
    retrainer = ModelRetrainer()
    logger.info("ETL monitor started — checking every 30 minutes")

    while True:
        try:
            for asset in ['gold', 'silver']:
                fresh = orch.freshness.check(asset)
                if fresh['is_fresh']:
                    logger.info(f"{asset} data fresh ({fresh['age_hours']}h old)")
                else:
                    logger.warning(f"{asset} data stale ({fresh['age_hours']}h old)")

            if retrainer.should_retrain(min_outcomes=10, accuracy_threshold=0.55):
                logger.info("Retrain conditions met — triggering")
                for asset in ['gold', 'silver']:
                    retrainer.retrain_model(asset)
        except Exception as e:
            logger.error(f"Monitor error: {e}")

        time.sleep(CHECK_INTERVAL)


if __name__ == '__main__':
    main()
