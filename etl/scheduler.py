"""Schedule and manage ETL pipeline execution."""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from typing import List, Optional, Dict, Any
import logging

from .pipeline import ETLPipeline
from .config import ETLConfig

logger = logging.getLogger(__name__)


class ETLScheduler:
    """Schedule and manage ETL pipeline execution."""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler(
            timezone='UTC',
            job_defaults={
                'coalesce': True,  # Combine multiple pending executions
                'max_instances': 1,  # Only one instance at a time
                'misfire_grace_time': 300  # 5 minutes grace period
            }
        )
        self.pipelines: Dict[str, ETLPipeline] = {}
        self.is_running = False
    
    def add_pipeline(
        self,
        pipeline: ETLPipeline,
        interval_minutes: int = 15,
        run_immediately: bool = False
    ):
        """
        Add pipeline to scheduler with interval trigger.
        
        Args:
            pipeline: ETLPipeline instance
            interval_minutes: Run every N minutes
            run_immediately: Run once immediately before scheduling
        """
        self.pipelines[pipeline.name] = pipeline
        
        self.scheduler.add_job(
            func=pipeline.run,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id=pipeline.name,
            name=pipeline.name,
            replace_existing=True
        )
        
        logger.info(f"✓ Scheduled '{pipeline.name}' every {interval_minutes} minutes")
        
        if run_immediately:
            logger.info(f"Running '{pipeline.name}' immediately...")
            pipeline.run()
    
    def add_daily_pipeline(
        self,
        pipeline: ETLPipeline,
        hour: int = 0,
        minute: int = 0
    ):
        """
        Add pipeline to run daily at specific time.
        
        Args:
            pipeline: ETLPipeline instance
            hour: Hour (0-23)
            minute: Minute (0-59)
        """
        self.pipelines[pipeline.name] = pipeline
        
        self.scheduler.add_job(
            func=pipeline.run,
            trigger=CronTrigger(hour=hour, minute=minute),
            id=pipeline.name,
            name=pipeline.name,
            replace_existing=True
        )
        
        logger.info(f"✓ Scheduled '{pipeline.name}' daily at {hour:02d}:{minute:02d} UTC")
    
    def add_cron_pipeline(
        self,
        pipeline: ETLPipeline,
        cron_expression: str
    ):
        """
        Add pipeline with cron expression.
        
        Args:
            pipeline: ETLPipeline instance
            cron_expression: Cron expression (e.g., '0 */4 * * *' for every 4 hours)
        """
        self.pipelines[pipeline.name] = pipeline
        
        self.scheduler.add_job(
            func=pipeline.run,
            trigger=CronTrigger.from_crontab(cron_expression),
            id=pipeline.name,
            name=pipeline.name,
            replace_existing=True
        )
        
        logger.info(f"✓ Scheduled '{pipeline.name}' with cron: {cron_expression}")
    
    def remove_pipeline(self, pipeline_name: str):
        """Remove pipeline from scheduler."""
        if pipeline_name in self.pipelines:
            del self.pipelines[pipeline_name]
            self.scheduler.remove_job(pipeline_name)
            logger.info(f"Removed pipeline: {pipeline_name}")
    
    def start(self):
        """Start the scheduler."""
        if not self.is_running:
            self.scheduler.start()
            self.is_running = True
            logger.info("=" * 80)
            logger.info("ETL Scheduler started")
            logger.info(f"Active pipelines: {len(self.pipelines)}")
            for name in self.pipelines.keys():
                logger.info(f"  - {name}")
            logger.info("=" * 80)
    
    def stop(self):
        """Stop the scheduler."""
        if self.is_running:
            self.scheduler.shutdown(wait=True)
            self.is_running = False
            logger.info("ETL Scheduler stopped")
    
    def pause(self):
        """Pause all jobs."""
        self.scheduler.pause()
        logger.info("Scheduler paused")
    
    def resume(self):
        """Resume all jobs."""
        self.scheduler.resume()
        logger.info("Scheduler resumed")
    
    def get_jobs(self) -> List[Dict[str, Any]]:
        """Get all scheduled jobs."""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        return jobs
    
    def get_pipeline_status(self, pipeline_name: str) -> Optional[Dict[str, Any]]:
        """Get status of specific pipeline."""
        if pipeline_name in self.pipelines:
            return self.pipelines[pipeline_name].get_status()
        return None
    
    def get_all_status(self) -> Dict[str, Any]:
        """Get status of all pipelines."""
        return {
            'scheduler_running': self.is_running,
            'total_pipelines': len(self.pipelines),
            'pipelines': {
                name: pipeline.get_status()
                for name, pipeline in self.pipelines.items()
            },
            'scheduled_jobs': self.get_jobs()
        }
