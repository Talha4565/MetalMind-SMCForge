"""Flask API routes for ETL pipeline management."""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
import threading
import logging

# Initialize global variables
etl_bp = Blueprint('etl', __name__, url_prefix='/api/etl')
logger = logging.getLogger(__name__)

# Global scheduler and pipeline status
scheduler = None
pipeline_status = {}
pipeline_threads = {}


def get_scheduler():
    """Get or create ETL scheduler instance."""
    global scheduler
    if scheduler is None:
        from etl.scheduler import ETLScheduler
        from etl.config import ETLConfig
        from etl.factory import PipelineFactory
        
        config = ETLConfig.from_env()
        scheduler = ETLScheduler()
        
        # Create and add pipelines
        gold_pipeline = PipelineFactory.create_gold_pipeline(config)
        silver_pipeline = PipelineFactory.create_silver_pipeline(config)
        
        scheduler.add_pipeline(gold_pipeline, interval_minutes=config.schedule_interval_minutes)
        scheduler.add_pipeline(silver_pipeline, interval_minutes=config.schedule_interval_minutes)
    
    return scheduler


@etl_bp.route('/run', methods=['POST'])
@jwt_required()
def run_pipeline():
    """
    Manually trigger ETL pipeline.
    
    Request body:
    {
        "asset": "gold" or "silver",
        "async": true/false
    }
    """
    try:
        data = request.get_json() or {}
        asset = data.get('asset', 'gold').lower()
        run_async = data.get('async', True)
        
        if asset not in ['gold', 'silver']:
            return jsonify({'error': 'Invalid asset. Must be "gold" or "silver"'}), 400
        
        from etl.config import ETLConfig
        from etl.factory import PipelineFactory
        
        config = ETLConfig.from_env()
        
        # Create pipeline
        if asset == 'gold':
            pipeline = PipelineFactory.create_gold_pipeline(config)
        else:
            pipeline = PipelineFactory.create_silver_pipeline(config)
        
        if run_async:
            # Run in background thread
            def run_and_store():
                result = pipeline.run()
                pipeline_status[asset] = {
                    'status': result.status.value,
                    'started_at': result.started_at.isoformat(),
                    'completed_at': result.completed_at.isoformat() if result.completed_at else None,
                    'records': result.records_processed,
                    'error': result.error,
                    'metrics': result.metrics
                }
            
            thread = threading.Thread(target=run_and_store, daemon=True)
            thread.start()
            pipeline_threads[asset] = thread
            
            return jsonify({
                'message': f'{asset.upper()} pipeline started',
                'status': 'running',
                'async': True
            }), 202
        else:
            # Run synchronously
            result = pipeline.run()
            
            return jsonify({
                'message': f'{asset.upper()} pipeline completed',
                'status': result.status.value,
                'records': result.records_processed,
                'duration': (result.completed_at - result.started_at).total_seconds() if result.completed_at else None,
                'error': result.error,
                'metrics': result.metrics
            }), 200 if result.status.value == 'success' else 500
    
    except Exception as e:
        logger.error(f"Pipeline run failed: {e}")
        return jsonify({'error': str(e)}), 500


@etl_bp.route('/status', methods=['GET'])
@jwt_required()
def get_status():
    """
    Get ETL pipeline status.
    
    Query params:
    - asset: Filter by asset (gold/silver)
    """
    try:
        asset = request.args.get('asset', '').lower()
        
        if asset and asset in pipeline_status:
            return jsonify({
                'asset': asset,
                'status': pipeline_status[asset]
            })
        
        return jsonify({
            'pipelines': pipeline_status,
            'scheduler_active': scheduler is not None and scheduler.is_running if scheduler else False
        })
    
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return jsonify({'error': str(e)}), 500


@etl_bp.route('/schedule', methods=['GET'])
@jwt_required()
def get_schedule():
    """Get scheduled ETL jobs."""
    try:
        sched = get_scheduler()
        
        return jsonify({
            'scheduler_running': sched.is_running,
            'jobs': sched.get_jobs(),
            'pipelines': {
                name: pipeline.get_status()
                for name, pipeline in sched.pipelines.items()
            }
        })
    
    except Exception as e:
        logger.error(f"Schedule check failed: {e}")
        return jsonify({'error': str(e)}), 500


@etl_bp.route('/schedule/start', methods=['POST'])
@jwt_required()
def start_scheduler():
    """Start the ETL scheduler."""
    try:
        sched = get_scheduler()
        
        if sched.is_running:
            return jsonify({'message': 'Scheduler is already running'}), 200
        
        sched.start()
        
        return jsonify({
            'message': 'Scheduler started',
            'jobs': sched.get_jobs()
        })
    
    except Exception as e:
        logger.error(f"Scheduler start failed: {e}")
        return jsonify({'error': str(e)}), 500


@etl_bp.route('/schedule/stop', methods=['POST'])
@jwt_required()
def stop_scheduler():
    """Stop the ETL scheduler."""
    try:
        global scheduler
        
        if scheduler is None or not scheduler.is_running:
            return jsonify({'message': 'Scheduler is not running'}), 200
        
        scheduler.stop()
        
        return jsonify({'message': 'Scheduler stopped'})
    
    except Exception as e:
        logger.error(f"Scheduler stop failed: {e}")
        return jsonify({'error': str(e)}), 500


@etl_bp.route('/metrics', methods=['GET'])
@jwt_required()
def get_metrics():
    """Get detailed ETL metrics."""
    try:
        sched = get_scheduler()
        
        metrics = {}
        for name, pipeline in sched.pipelines.items():
            metrics[name] = pipeline.get_metrics()
        
        return jsonify({'metrics': metrics})
    
    except Exception as e:
        logger.error(f"Metrics retrieval failed: {e}")
        return jsonify({'error': str(e)}), 500


@etl_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint — returns minimal status info, no auth required."""
    try:
        global scheduler
        is_running = scheduler.is_running if scheduler else False

        return jsonify({
            'status': 'healthy',
            'scheduler_running': is_running
        })

    except Exception as e:
        return jsonify({'status': 'unhealthy'}), 500
