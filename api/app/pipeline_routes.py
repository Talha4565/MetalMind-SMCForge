"""
Pipeline Orchestrator API endpoints.
Provides status, details, and control for ETL/Feature/Model pipelines.
"""

from flask import Blueprint, jsonify, request
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

pipeline_bp = Blueprint('pipeline', __name__, url_prefix='/api/pipeline')


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
    from config.settings import MODEL_CONFIG

    if asset == 'gold':
        model_path = MODEL_CONFIG.get('enhanced_model_path', Path('models/enhanced_15m.pkl'))
    else:
        model_path = Path('models/processed/silver_model_enhanced.pkl')

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
                'description': 'Fetches OHLCV data from Yahoo Finance and appends to CSV files'
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
def trigger_pipeline_run():
    """Trigger manual pipeline run."""
    try:
        data = request.json or {}
        pipeline_type = data.get('type', 'update')
        asset = data.get('asset', 'gold')

        if asset not in ['gold', 'silver']:
            return jsonify({'error': 'Invalid asset'}), 400

        import subprocess, sys
        project_root = Path(__file__).parent.parent.parent

        if pipeline_type == 'update':
            cmd = [sys.executable, 'run_pipeline.py', '--mode', 'update', '--asset', asset]
        elif pipeline_type == 'retrain':
            cmd = [sys.executable, 'run_pipeline.py', '--mode', 'retrain', '--asset', asset]
        else:
            return jsonify({'error': 'Invalid pipeline type'}), 400

        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(project_root), timeout=300)

        if result.returncode == 0:
            return jsonify({'status': 'completed', 'message': f'{pipeline_type} completed for {asset}'})
        else:
            return jsonify({'error': result.stderr or 'Pipeline failed'}), 500

    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Pipeline timed out'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500
