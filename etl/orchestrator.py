"""
Pipeline Orchestrator — manages data freshness, model versioning, health monitoring, and status tracking.
"""

import json
import shutil
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


# ============================================================================
# 1. DATA FRESHNESS CHECK
# ============================================================================

class DataFreshnessChecker:
    """Verify CSV data is fresh enough for retraining."""
    
    def __init__(self, max_age_hours: int = 25):
        self.max_age_hours = max_age_hours
    
    def check(self, asset: str) -> Dict[str, Any]:
        """
        Check if CSV data is fresh enough for retraining.
        
        Returns dict with:
        - is_fresh: bool
        - last_date: str (ISO format)
        - age_hours: float
        - rows: int
        - message: str
        """
        from config.settings import GOLD_DATASET_DIR, SILVER_DATASET_DIR
        import pandas as pd
        
        data_dir = GOLD_DATASET_DIR if asset == 'gold' else SILVER_DATASET_DIR
        csv_path = data_dir / f"{asset.title()}_15m_Candlestick.csv"
        
        if not csv_path.exists():
            return {
                'is_fresh': False,
                'last_date': None,
                'age_hours': float('inf'),
                'rows': 0,
                'message': f'CSV not found: {csv_path}'
            }
        
        try:
            df = pd.read_csv(csv_path)
            last_date = pd.to_datetime(df['Date'].iloc[-1])
            now = pd.Timestamp.now()
            age_hours = (now - last_date).total_seconds() / 3600
            
            is_fresh = age_hours <= self.max_age_hours
            
            return {
                'is_fresh': is_fresh,
                'last_date': last_date.isoformat(),
                'age_hours': round(age_hours, 1),
                'rows': len(df),
                'message': f'Data is {age_hours:.1f}h old (max: {self.max_age_hours}h)'
            }
        except Exception as e:
            return {
                'is_fresh': False,
                'last_date': None,
                'age_hours': float('inf'),
                'rows': 0,
                'message': f'Error checking freshness: {e}'
            }


# ============================================================================
# 2. MODEL VERSIONING
# ============================================================================

class ModelVersionManager:
    """Manage model versions with backup and rollback."""
    
    def __init__(self, models_dir: str = None):
        from config.settings import MODELS_DIR
        self.models_dir = Path(models_dir) if models_dir else MODELS_DIR
        self.backup_dir = self.models_dir / 'backups'
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self, asset: str) -> Optional[str]:
        """Create backup of current model before retraining."""
        model_path = self.models_dir / f'enhanced_15m.pkl' if asset == 'gold' else \
                     self.models_dir / 'processed' / 'silver_model_enhanced.pkl'
        
        if not model_path.exists():
            logger.warning(f"No model to backup for {asset}")
            return None
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f'{asset}_model_{timestamp}.pkl'
        backup_path = self.backup_dir / backup_name
        
        shutil.copy2(model_path, backup_path)
        logger.info(f"✓ Backup created: {backup_name}")
        
        # Keep only last 5 backups per asset
        self._cleanup_backups(asset, keep=5)
        
        return str(backup_path)
    
    def rollback(self, asset: str) -> bool:
        """Rollback to the most recent backup."""
        backups = sorted(self.backup_dir.glob(f'{asset}_model_*.pkl'), reverse=True)
        
        if not backups:
            logger.error(f"No backups found for {asset}")
            return False
        
        latest_backup = backups[0]
        model_path = self.models_dir / f'enhanced_15m.pkl' if asset == 'gold' else \
                     self.models_dir / 'processed' / 'silver_model_enhanced.pkl'
        
        shutil.copy2(latest_backup, model_path)
        logger.info(f"✓ Rolled back {asset} to {latest_backup.name}")
        return True
    
    def list_backups(self, asset: str = None) -> list:
        """List available backups."""
        pattern = f'{asset}_model_*.pkl' if asset else '*_model_*.pkl'
        backups = sorted(self.backup_dir.glob(pattern), reverse=True)
        
        return [
            {
                'name': b.name,
                'asset': b.name.split('_model_')[0],
                'timestamp': b.name.split('_model_')[1].replace('.pkl', ''),
                'size_mb': round(b.stat().st_size / 1024 / 1024, 2)
            }
            for b in backups
        ]
    
    def _cleanup_backups(self, asset: str, keep: int = 5):
        """Keep only the last N backups per asset."""
        backups = sorted(self.backup_dir.glob(f'{asset}_model_*.pkl'))
        
        if len(backups) > keep:
            for old_backup in backups[:-keep]:
                old_backup.unlink()
                logger.info(f"Cleaned old backup: {old_backup.name}")


# ============================================================================
# 3. HEALTH MONITORING
# ============================================================================

@dataclass
class PipelineHealth:
    """Health status of the pipeline."""
    last_update: Optional[str] = None
    last_retrain: Optional[str] = None
    update_status: str = 'unknown'
    retrain_status: str = 'unknown'
    update_error: Optional[str] = None
    retrain_error: Optional[str] = None
    consecutive_failures: int = 0
    uptime_since: Optional[str] = None


class HealthMonitor:
    """Track pipeline health and alert on failures."""
    
    def __init__(self, health_file: str = None):
        from config.settings import REPORTS_DIR
        self.health_file = Path(health_file) if health_file else REPORTS_DIR / 'pipeline_health.json'
        self.health_file.parent.mkdir(parents=True, exist_ok=True)
        self.health = PipelineHealth(uptime_since=datetime.now().isoformat())
        self._load()
    
    def record_update(self, success: bool, error: str = None):
        """Record data update result."""
        self.health.last_update = datetime.now().isoformat()
        self.health.update_status = 'success' if success else 'failed'
        self.health.update_error = error
        
        if success:
            self.health.consecutive_failures = 0
        else:
            self.health.consecutive_failures += 1
        
        self._save()
        
        # Alert on consecutive failures
        if self.health.consecutive_failures >= 3:
            self._alert(f"Pipeline failed {self.health.consecutive_failures} times in a row!")
    
    def record_retrain(self, success: bool, error: str = None, metrics: dict = None):
        """Record retrain result."""
        self.health.last_retrain = datetime.now().isoformat()
        self.health.retrain_status = 'success' if success else 'failed'
        self.health.retrain_error = error
        
        if success:
            self.health.consecutive_failures = 0
        else:
            self.health.consecutive_failures += 1
        
        self._save()
        
        if self.health.consecutive_failures >= 3:
            self._alert(f"Retrain failed {self.health.consecutive_failures} times in a row!")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current health status."""
        return asdict(self.health)
    
    def _alert(self, message: str):
        """Send health alert (log + email)."""
        logger.critical(f"🚨 HEALTH ALERT: {message}")
        
        try:
            from etl.alerts import EmailAlertService
            alerts = EmailAlertService()
            if alerts.enabled:
                # Send as a special alert (not a trading signal)
                import smtplib
                import ssl
                from email.mime.text import MIMEText
                
                msg = MIMEText(f"MetalMind Pipeline Health Alert\n\n{message}\n\nTime: {datetime.now().isoformat()}")
                msg['Subject'] = f"🚨 Pipeline Alert: {message[:50]}"
                msg['From'] = alerts.sender_email
                msg['To'] = alerts.recipient_email
                
                context = ssl.create_default_context()
                with smtplib.SMTP(alerts.smtp_host, alerts.smtp_port) as server:
                    server.starttls(context=context)
                    server.login(alerts.sender_email, alerts.sender_password)
                    server.sendmail(alerts.sender_email, alerts.recipient_email, msg.as_string())
                
                logger.info("Health alert email sent")
        except Exception as e:
            logger.warning(f"Could not send health alert email: {e}")
    
    def _save(self):
        """Save health status to file."""
        with open(self.health_file, 'w') as f:
            json.dump(asdict(self.health), f, indent=2)
    
    def _load(self):
        """Load health status from file."""
        if self.health_file.exists():
            try:
                with open(self.health_file, 'r') as f:
                    data = json.load(f)
                self.health = PipelineHealth(**data)
            except Exception:
                pass


# ============================================================================
# 4. PIPELINE STATUS TRACKER
# ============================================================================

class PipelineStatusTracker:
    """Track and expose pipeline status for dashboard/API."""
    
    def __init__(self, status_file: str = None):
        from config.settings import REPORTS_DIR
        self.status_file = Path(status_file) if status_file else REPORTS_DIR / 'pipeline_status.json'
        self.status_file.parent.mkdir(parents=True, exist_ok=True)
        self._load()
    
    def update_job_status(self, job_id: str, status: str, result: Any = None, error: str = None):
        """Update status of a scheduled job."""
        now = datetime.now().isoformat()
        
        if status == 'running':
            self._status[job_id] = {
                'status': 'running',
                'started_at': now,
                'completed_at': None,
                'result': None,
                'error': None,
            }
        elif status == 'success':
            self._status[job_id]['status'] = 'success'
            self._status[job_id]['completed_at'] = now
            self._status[job_id]['result'] = result
            self._status[job_id]['last_success'] = now
        elif status == 'failed':
            self._status[job_id]['status'] = 'failed'
            self._status[job_id]['completed_at'] = now
            self._status[job_id]['error'] = error
        
        self._save()
    
    def get_status(self) -> Dict[str, Any]:
        """Get full pipeline status for dashboard."""
        self._load()
        
        return {
            'last_updated': datetime.now().isoformat(),
            'jobs': self._status,
            'summary': self._summarize()
        }
    
    def _summarize(self) -> Dict[str, Any]:
        """Summarize job statuses."""
        total = len(self._status)
        running = sum(1 for j in self._status.values() if j.get('status') == 'running')
        success = sum(1 for j in self._status.values() if j.get('status') == 'success')
        failed = sum(1 for j in self._status.values() if j.get('status') == 'failed')
        
        return {
            'total_jobs': total,
            'running': running,
            'success': success,
            'failed': failed,
            'health': 'healthy' if failed == 0 else 'degraded' if failed < total else 'critical'
        }
    
    def _save(self):
        """Save status to file."""
        with open(self.status_file, 'w') as f:
            json.dump(self._status, f, indent=2, default=str)
    
    def _load(self):
        """Load status from file."""
        if self.status_file.exists():
            try:
                with open(self.status_file, 'r') as f:
                    self._status = json.load(f)
            except Exception:
                self._status = {}
        else:
            self._status = {}


# ============================================================================
# ORCHESTRATOR — ties everything together
# ============================================================================

class PipelineOrchestrator:
    """Main orchestrator that ties freshness, versioning, health, and status together."""
    
    def __init__(self):
        self.freshness = DataFreshnessChecker(max_age_hours=25)
        self.versioning = ModelVersionManager()
        self.health = HealthMonitor()
        self.status = PipelineStatusTracker()
    
    def run_update(self, asset: str) -> bool:
        """Run data update with health tracking."""
        job_id = f'{asset}_update'
        self.status.update_job_status(job_id, 'running')
        
        try:
            from run_pipeline import run_fetch_and_append
            run_fetch_and_append(asset)
            
            # Check freshness after update
            freshness = self.freshness.check(asset)
            self.health.record_update(
                success=freshness['is_fresh'],
                error=freshness['message'] if not freshness['is_fresh'] else None
            )
            self.status.update_job_status(job_id, 'success', result=freshness)
            
            return True
        except Exception as e:
            self.health.record_update(success=False, error=str(e))
            self.status.update_job_status(job_id, 'failed', error=str(e))
            return False
    
    def run_retrain(self, asset: str, trials: int = 10) -> bool:
        """Run retrain with backup and health tracking."""
        job_id = f'{asset}_retrain'
        self.status.update_job_status(job_id, 'running')
        
        try:
            # Create backup before retraining
            self.versioning.create_backup(asset)
            
            # Run retrain
            from models.retrain import retrain_model
            result = retrain_model(asset, trials)
            
            success = result.get('status') == 'success'
            self.health.record_retrain(
                success=success,
                error=result.get('error'),
                metrics={'accuracy': result.get('accuracy')}
            )
            self.status.update_job_status(job_id, 'success', result=result)
            
            return success
        except Exception as e:
            self.health.record_retrain(success=False, error=str(e))
            self.status.update_job_status(job_id, 'failed', error=str(e))
            
            # Rollback on failure
            logger.error(f"Retrain failed, rolling back {asset}...")
            self.versioning.rollback(asset)
            
            return False
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get all data needed for pipeline dashboard."""
        return {
            'health': self.health.get_status(),
            'status': self.status.get_status(),
            'freshness': {
                'gold': self.freshness.check('gold'),
                'silver': self.freshness.check('silver'),
            },
            'backups': self.versioning.list_backups(),
        }
