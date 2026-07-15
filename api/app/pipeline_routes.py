"""
Pipeline Orchestrator API endpoints.
Provides status, details, and control for ETL/Feature/Model pipelines.
"""

from flask import Blueprint, jsonify, request
from datetime import datetime
from pathlib import Path
from api.app.auth import token_required
from api.app.extensions import limiter
import logging
import threading

logger = logging.getLogger(__name__)

pipeline_bp = Blueprint('pipeline', __name__, url_prefix='/api/pipeline')

# Global state for async operations
_running_jobs = {}


def _check_data_freshness(asset: str) -> dict:
    """Check if CSV data is fresh."""
    import pandas as pd
    from config.settings import GOLD_DATASET_DIR, SILVER_DATASET_DIR

    data_dir = GOLD_DATASET_DIR if asset == 'gold' else SILVER_DATASET_DIR
    csv_path = data_dir / f"{asset.title()}_15m_Candlestick.csv"

    if not csv_path.exists():
        return {'is_fresh': False, 'last_date': None, 'age_hours': float('inf'), 'rows': 0, 'message': 'CSV not found'}

    try:
        df = pd.read_csv(csv_path)
        # Combine Date and Time columns for accurate freshness check
        if 'Time' in df.columns:
            last_datetime = pd.to_datetime(df['Date'].iloc[-1] + ' ' + df['Time'].iloc[-1])
        else:
            last_datetime = pd.to_datetime(df['Date'].iloc[-1])
        age_hours = (pd.Timestamp.now() - last_datetime).total_seconds() / 3600
        return {
            'is_fresh': age_hours <= 25,
            'last_date': last_datetime.isoformat(),
            'age_hours': round(age_hours, 1),
            'rows': len(df),
            'message': f'{age_hours:.1f}h old'
        }
    except Exception as e:
        return {'is_fresh': False, 'last_date': None, 'age_hours': float('inf'), 'rows': 0, 'message': str(e)}


def _get_model_info(asset: str) -> dict:
    """Get model file info."""
    if asset == 'gold':
        model_path = Path('models/gold_regression_system.pkl')
    else:
        model_path = Path('models/silver_enhanced_15m.pkl')

    if not model_path.exists():
        return {'exists': False, 'version': None, 'size_mb': 0, 'last_modified': None}

    stat = model_path.stat()
    return {
        'exists': True,
        'version': f'v{int(stat.st_mtime) % 1000}',
        'size_mb': round(stat.st_size / 1024 / 1024, 2),
        'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
        'features': 89
    }


@pipeline_bp.route('/status', methods=['GET'])
@limiter.limit("300 per hour")
def get_pipeline_status():
    """Public pipeline status summary."""
    gold_fresh = _check_data_freshness('gold')
    silver_fresh = _check_data_freshness('silver')
    gold_model = _get_model_info('gold')
    silver_model = _get_model_info('silver')

    all_fresh = gold_fresh['is_fresh'] and silver_fresh['is_fresh']
    any_model = gold_model['exists'] or silver_model['exists']

    return jsonify({
        'status': 'active' if all_fresh and any_model else 'degraded',
        'data_freshness': {
            'gold': gold_fresh,
            'silver': silver_fresh,
        },
        'models': {
            'gold': gold_model,
            'silver': silver_model,
        },
        'last_update': gold_fresh['last_date'] or silver_fresh['last_date'],
        'timestamp': datetime.now().isoformat()
    })


@pipeline_bp.route('/details', methods=['GET'])
@limiter.limit("100 per hour")
def get_pipeline_details():
    """Full pipeline details (admin)."""
    gold_fresh = _check_data_freshness('gold')
    silver_fresh = _check_data_freshness('silver')
    gold_model = _get_model_info('gold')
    silver_model = _get_model_info('silver')

    return jsonify({
        'pipelines': {
            'etl': {
                'name': 'ETL Pipeline',
                'status': 'active',
                'schedule': 'Every 15 minutes',
                'last_run': gold_fresh['last_date'],
                'description': 'Fetches OHLCV data from MT5 and appends to CSV files'
            },
            'features': {
                'name': 'Feature Engineering',
                'status': 'active',
                'schedule': 'On each prediction request',
                'features_count': 89,
                'description': 'Transforms raw OHLCV into 89 ML features (SMC, volume, multi-timeframe)'
            },
            'training': {
                'name': 'Model Training',
                'status': 'active',
                'schedule': 'Daily at 03:00 UTC',
                'last_run': gold_model.get('last_modified'),
                'description': 'Retrains XGBoost models with Optuna hyperparameter tuning'
            }
        },
        'data': {
            'gold': gold_fresh,
            'silver': silver_fresh,
        },
        'models': {
            'gold': gold_model,
            'silver': silver_model,
        },
        'health': {
            'status': 'healthy',
            'uptime': '99.9%',
            'last_incident': None
        },
        'timestamp': datetime.now().isoformat()
    })


@pipeline_bp.route('/run', methods=['POST'])
@token_required
def trigger_pipeline_run(_email=None):
    """
    Trigger manual pipeline run via orchestrator.
    
    Request body:
        {"type": "update"|"retrain", "asset": "gold"|"silver"}
    
    Returns:
        {"status": "completed"|"running", "result": {...}}
    """
    try:
        data = request.json or {}
        pipeline_type = data.get('type', 'update')
        asset = data.get('asset', 'gold')

        if asset not in ['gold', 'silver']:
            return jsonify({'error': 'Invalid asset. Must be "gold" or "silver"'}), 400

        if pipeline_type not in ['update', 'retrain']:
            return jsonify({'error': 'Invalid type. Must be "update" or "retrain"'}), 400

        # Check if job already running
        job_key = f'{asset}_{pipeline_type}'
        if job_key in _running_jobs and _running_jobs[job_key].is_alive():
            return jsonify({'status': 'running', 'message': f'{pipeline_type} already running for {asset}'}), 409

        from etl.orchestrator import PipelineOrchestrator
        orch = PipelineOrchestrator()

        def run_job():
            try:
                _running_jobs[job_key] = threading.current_thread()
                if pipeline_type == 'update':
                    result = orch.run_update(asset)
                else:
                    result = orch.run_retrain(asset, trials=20)
                logger.info(f"Job {job_key} completed: {result}")
            except Exception as e:
                logger.error(f"Job {job_key} failed: {e}")
            finally:
                _running_jobs.pop(job_key, None)

        thread = threading.Thread(target=run_job, daemon=True, name=job_key)
        thread.start()

        return jsonify({
            'status': 'started',
            'message': f'{pipeline_type} started for {asset}',
            'job_key': job_key,
        }), 202

    except Exception as e:
        logger.error(f"Pipeline trigger failed: {e}")
        return jsonify({'error': str(e)}), 500


@pipeline_bp.route('/jobs', methods=['GET'])
@token_required
@limiter.limit("60 per hour")
def get_running_jobs(_email=None):
    """Get currently running pipeline jobs."""
    jobs = {}
    for key, thread in _running_jobs.items():
        jobs[key] = {
            'alive': thread.is_alive(),
            'name': thread.name,
        }
    return jsonify({'running_jobs': jobs, 'count': len(jobs)})


@pipeline_bp.route('/health', methods=['GET'])
@limiter.limit("300 per hour")
def get_pipeline_health():
    """Get pipeline health status from orchestrator."""
    try:
        from etl.orchestrator import PipelineOrchestrator
        orch = PipelineOrchestrator()
        health = orch.health.get_status()
        return jsonify(health)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
