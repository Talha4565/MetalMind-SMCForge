"""
Flask API for ML Signals Dashboard
Serves predictions, backtest results, and SHAP explainability data.
"""

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_compress import Compress  # FIXED: Add compression
from flask_socketio import SocketIO, emit
import pickle
import pandas as pd
import json  # FIXED: Removed duplicate import
from pathlib import Path
import logging
import sys
from functools import lru_cache
from datetime import datetime, timedelta, timezone
import threading

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data.loaders import load_gold_data, load_silver_data, load_asset_data
from features.pipeline import engineer_all_features

# Import database and authentication
from api.app.database import init_database
from api.app.auth import init_auth, token_required
from api.app.watchlist import watchlist_bp
from api.app.profile import profile_bp
from api.app.middleware.error_handler import register_error_handlers
from api.app.etl_routes import etl_bp
from api.app.etl_dashboard import dashboard_bp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize SocketIO for real-time features
socketio = SocketIO(app, cors_allowed_origins=["http://localhost:3000"])

# FIXED: Register centralized error handlers
register_error_handlers(app)


@app.after_request
def set_security_headers(response):
    """Add security headers to every response."""
    # Content Security Policy — restrict resource loading to known safe origins
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.tailwindcss.com https://cdnjs.cloudflare.com; "
        "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
        "img-src 'self' data:; "
        "connect-src 'self'; "
        "frame-ancestors 'none';"
    )
    # Prevent clickjacking
    response.headers['X-Frame-Options'] = 'DENY'
    # Prevent MIME-type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    # Force HTTPS in production
    if app.config.get('ENV') == 'production':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    # Limit referrer info sent to third parties
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    # Disable browser features not needed by the app
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    return response

# FIXED: Configure CORS properly - allow specific origins
# Next.js frontend served from port 3000
CORS(app,
     resources={r"/api/*": {
         "origins": [
             "http://localhost:3000",  # Next.js dev server
             "https://yourdomain.com"  # Production (change this)
         ],
         "supports_credentials": True,
         "methods": ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
         "allow_headers": ['Content-Type', 'Authorization'],
         "expose_headers": ['Content-Type', 'Authorization']
     }}
)

# FIXED: Enable response compression for all endpoints
Compress(app)

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Limit request body size — 2MB max (prevents DoS via large payloads)
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

# Initialize database FIRST (auth depends on it)
init_database(app)

# Initialize authentication
init_auth(app)

# Register additional blueprints
app.register_blueprint(watchlist_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(etl_bp)
app.register_blueprint(dashboard_bp)


# FIXED: Encapsulate all global state in proper classes for thread safety and testability
MODELS_DIR = Path(__file__).parent.parent.parent / 'models'

class ModelManager:
    """Thread-safe model management with lazy loading."""
    
    def __init__(self):
        self._models = {}
        self._feature_names = {}
        self._lock = threading.Lock()
        self.models_dir = MODELS_DIR
    
    def load_model(self, asset: str) -> tuple:
        """Load model for specific asset."""
        if asset == "gold":
            model_path = self.models_dir / 'enhanced_15m.pkl'
        elif asset == "silver":
            model_path = self.models_dir / 'processed' / 'silver_model_enhanced.pkl'
        else:
            return None, None
        
        if not model_path.exists():
            logger.warning(f"⚠️ Model file not found for {asset}: {model_path}")
            return None, None
        
        try:
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
                
                # Handle different pickle formats
                if isinstance(model_data, dict):
                    model = model_data['model']
                    feature_names = model_data.get('features', None)
                else:
                    # If it's just the model object
                    model = model_data
                    try:
                        feature_names = list(model.feature_names_in_) if hasattr(model, 'feature_names_in_') else None
                    except:
                        feature_names = None
            
            if feature_names is not None:
                logger.info(f"✅ {asset.upper()} model loaded: {len(feature_names)} features")
            else:
                logger.info(f"✅ {asset.upper()} model loaded (feature names will be inferred)")
            
            return model, feature_names
        
        except Exception as e:
            logger.error(f"❌ Failed to load {asset} model: {e}")
            import traceback
            traceback.print_exc()
            return None, None
    
    def get_or_load_model(self, asset: str) -> tuple:
        """Get model, loading it lazily if needed. Thread-safe."""
        with self._lock:
            if asset not in self._models:
                logger.info(f"Lazy loading {asset} model...")
                self._models[asset], self._feature_names[asset] = self.load_model(asset)
                if self._models[asset] is None:
                    logger.warning(f"⚠️ Model not found for {asset}. Train it first.")
            return self._models.get(asset), self._feature_names.get(asset)
    
    def is_loaded(self, asset: str) -> bool:
        """Check if model is loaded."""
        with self._lock:
            return asset in self._models and self._models[asset] is not None
    
    def get_loaded_models(self) -> dict:
        """Get status of all models."""
        with self._lock:
            return {asset: (self._models.get(asset) is not None) for asset in ['gold', 'silver']}


class PredictionCache:
    """Thread-safe prediction cache with TTL."""
    
    def __init__(self, ttl_seconds=60):
        self._cache = {}
        self._lock = threading.Lock()
        self._ttl = ttl_seconds
    
    def get(self, key: str):
        """Get cached data if still valid."""
        with self._lock:
            if key in self._cache:
                data, cache_time = self._cache[key]
                if (datetime.utcnow() - cache_time).total_seconds() < self._ttl:
                    return data
        return None
    
    def set(self, key: str, data):
        """Set cached data with current timestamp."""
        with self._lock:
            self._cache[key] = (data, datetime.utcnow())
    
    def clear(self, key: str = None):
        """Clear cache (specific key or all)."""
        with self._lock:
            if key:
                self._cache.pop(key, None)
            else:
                self._cache.clear()


class FileCache:
    """Thread-safe file cache with TTL and mtime checking."""
    
    def __init__(self, ttl_seconds=60):
        self._cache = {}
        self._lock = threading.Lock()
        self._ttl = ttl_seconds
    
    def get_json(self, filepath: Path):
        """Get cached JSON file content if still valid."""
        with self._lock:
            if not filepath.exists():
                return None
            
            current_mtime = filepath.stat().st_mtime
            cache_key = str(filepath)
            
            if cache_key in self._cache:
                data, cache_time, cached_mtime = self._cache[cache_key]
                
                # Check if cache is still valid (TTL and file not modified)
                age = (datetime.utcnow() - cache_time).total_seconds()
                if age < self._ttl and current_mtime == cached_mtime:
                    return data
            
            # Cache miss or expired - load file
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                self._cache[cache_key] = (data, datetime.utcnow(), current_mtime)
                return data
            except Exception as e:
                logger.error(f"Failed to load JSON file {filepath}: {e}")
                return None
    
    def clear(self):
        """Clear all cached files."""
        with self._lock:
            self._cache.clear()


class BacktestManager:
    """Thread-safe backtest execution manager."""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._status = {'running': False, 'progress': 0, 'error': None}
    
    def is_running(self) -> bool:
        """Check if backtest is currently running."""
        with self._lock:
            return self._status['running']

    def get_status(self) -> dict:
        """Get current backtest status."""
        with self._lock:
            return self._status.copy()

    def run(self, start_date: str, end_date: str) -> dict:
        """Run backtest with lock. Returns result dict."""
        with self._lock:
            if self._status['running']:
                return {'error': 'Backtest already running', 'status': self._status}, 409
            self._status = {'running': True, 'progress': 0, 'error': None}

        try:
            import subprocess, sys
            project_root = Path(__file__).parent.parent.parent
            result = subprocess.run(
                [sys.executable, 'run.py', '--mode', 'backtest'],
                capture_output=True,
                text=True,
                cwd=str(project_root),
                timeout=300
            )

            if result.returncode == 0:
                with self._lock:
                    self._status = {'running': False, 'progress': 100, 'error': None}
                return {'status': 'completed', 'message': 'Backtest completed successfully'}, 200
            else:
                error_msg = result.stderr or 'Unknown error'
                with self._lock:
                    self._status = {'running': False, 'progress': 0, 'error': error_msg}
                return {'error': f'Backtest failed: {error_msg}'}, 500

        except subprocess.TimeoutExpired:
            with self._lock:
                self._status = {'running': False, 'progress': 0, 'error': 'Timeout'}
            return {'error': 'Backtest timed out after 5 minutes'}, 500
        except Exception as e:
            with self._lock:
                self._status = {'running': False, 'progress': 0, 'error': str(e)}
            return {'error': f'Backtest error: {str(e)}'}, 500


# FIXED: Initialize managers (no global dicts!)
model_manager = ModelManager()
prediction_cache = PredictionCache(ttl_seconds=60)
backtest_manager = BacktestManager()
file_cache = FileCache(ttl_seconds=60)  # FIXED: Cache for JSON files

logger.info("✅ Server ready - models will be loaded on first request (lazy loading)")
logger.info("✅ ModelManager, PredictionCache, and BacktestManager initialized")


@app.route('/api/health', methods=['GET'])
@limiter.limit("10 per minute")
def health_check():
    """FIXED: Enhanced health check with comprehensive status."""
    try:
        # Check database connection
        db_healthy = False
        try:
            from api.app.database import db
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            db_healthy = True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
        
        # Get model status
        models_status = model_manager.get_loaded_models()
        
        # Check file system access (use absolute paths from project root)
        project_root = Path(__file__).parent.parent.parent
        fs_healthy = (project_root / 'reports').exists() and (project_root / 'models').exists()
        
        # Overall health - filesystem is not critical, just log warning
        overall_healthy = db_healthy  # Only DB is critical for health
        
        return jsonify({
            'status': 'healthy' if overall_healthy else 'degraded',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'checks': {
                'database': 'ok' if db_healthy else 'error',
                'filesystem': 'ok' if fs_healthy else 'error',
                'models': models_status
            },
            'version': '1.0.0'
        }), 200 if overall_healthy else 503
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 503


@app.route('/api/predictions/latest', methods=['GET'])
@token_required
@limiter.limit("100 per minute")  # FIXED: Add rate limiting
def get_latest_predictions(current_user_email):
    """Get latest predictions for live monitoring.
    
    Query params:
        asset: Asset to get predictions for (gold or silver, default: gold)
        limit: Number of recent bars to return (default: 100)
    """
    try:
        # Get parameters
        asset = request.args.get('asset', 'gold').lower()
        
        # FIXED: Validate limit parameter to prevent DoS
        try:
            limit = int(request.args.get('limit', 100))
            if limit < 1 or limit > 1000:
                return jsonify({'error': 'Limit must be between 1 and 1000'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid limit parameter'}), 400
        
        # Validate asset
        if asset not in ['gold', 'silver']:
            return jsonify({'error': 'Invalid asset. Must be "gold" or "silver"'}), 400
        
        # FIXED: Use ModelManager for lazy loading
        model, feature_names = model_manager.get_or_load_model(asset)
        if model is None:
            return jsonify({'error': f'Model not found for {asset}. Train it first.'}), 404
        
        # FIXED: Use PredictionCache manager
        cache_key = f"{asset}_predictions"
        df = prediction_cache.get(cache_key)
        
        if df is None:
            logger.info(f"Loading {asset} data for predictions...")
            df = load_asset_data(asset=asset, primary_tf='15m', session_filter=True)
            
            # Apply feature engineering
            df = engineer_all_features(df, add_labels=False)
            
            # Cache the engineered data
            prediction_cache.set(cache_key, df)
        else:
            logger.info(f"Using cached data for {asset}")
        
        # Get most recent N bars
        recent_data = df.iloc[-limit:].copy()
        
        # Use all feature columns except datetime/target if feature_names not available
        if feature_names is not None:
            X = recent_data[feature_names]
        else:
            # Get all numeric columns as features
            X = recent_data.select_dtypes(include=['float64', 'int64'])
        
        # Get predictions and probabilities
        predictions = model.predict(X)
        probabilities = model.predict_proba(X)[:, 1]  # Probability of signal
        
        # Prepare response
        results = []
        for i, (idx, row) in enumerate(recent_data.iterrows()):
            results.append({
                'timestamp': idx.isoformat(),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'signal': int(predictions[i]),
                'probability': float(probabilities[i])
            })
        
        return jsonify({
            'asset': asset,
            'predictions': results,
            'total_signals': int(predictions.sum()),
            'data_range': {
                'start': recent_data.index.min().isoformat(),
                'end': recent_data.index.max().isoformat()
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting predictions: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/backtest/results', methods=['GET'])
@token_required
@limiter.limit("60 per minute")  # FIXED: Add rate limiting
def get_backtest_results(current_user_email):
    """Get backtest results.
    
    Query params:
        asset: Asset to get backtest for (gold, silver, or latest, default: latest)
    """
    try:
        asset = request.args.get('asset', 'latest').lower()
        
        # FIXED: Whitelist validation to prevent path traversal
        ALLOWED_ASSETS = {'gold', 'silver', 'latest'}
        if asset not in ALLOWED_ASSETS:
            return jsonify({
                'error': f'Invalid asset. Must be one of: {", ".join(ALLOWED_ASSETS)}'
            }), 400
        
        # FIXED: Use safe mapping instead of string concatenation
        asset_file_map = {
            'gold': 'gold_backtest.json',
            'silver': 'latest.json',
            'latest': 'latest.json'
        }

        # Construct absolute path safely (works both locally and in Docker)
        project_root = Path(__file__).parent.parent.parent
        results_file = project_root / 'reports' / 'backtest_results' / asset_file_map[asset]
        
        if not results_file.exists():
            return jsonify({'error': f'No backtest results found for {asset}. Run backtest first.'}), 404
        
        with open(results_file, 'r') as f:
            data = json.load(f)
        
        # Add asset identifier to response
        data['asset'] = asset if asset in ['gold', 'silver'] else 'latest'
        
        return jsonify(data)
    
    except Exception as e:
        logger.error(f"Error loading backtest results: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/backtest/run', methods=['POST'])
@token_required
@limiter.limit("1 per hour")  # FIXED: Limit to 1 backtest per hour per user
def run_backtest(current_user_email):
    """Run backtest with specified parameters."""
    try:
        params = request.json
        start_date = params.get('start_date')
        end_date = params.get('end_date')
        
        logger.info(f"Running backtest from {start_date} to {end_date}")
        
        # FIXED: Use BacktestManager for thread-safe execution
        result, status_code = backtest_manager.run(start_date, end_date)
        return jsonify(result), status_code
    
    except Exception as e:
        logger.error(f"Error starting backtest: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/shap/feature-importance', methods=['GET'])
@token_required
@limiter.limit("60 per minute")  # FIXED: Add rate limiting
def get_shap_feature_importance(current_user_email):
    """Get SHAP feature importance data."""
    try:
        # Load SHAP values if they exist (absolute path — works in Docker)
        project_root = Path(__file__).parent.parent.parent
        shap_file = project_root / 'reports' / 'shap_plots' / 'shap_values.json'
        
        if shap_file.exists():
            with open(shap_file, 'r') as f:
                data = json.load(f)
            return jsonify(data)
        else:
            # Return mock data if SHAP analysis hasn't been run
            return jsonify({
                'feature_importance': [
                    {'feature': 'vwap_distance_5m', 'importance': 0.15},
                    {'feature': 'vwap_distance_15m', 'importance': 0.12},
                    {'feature': 'volume_imbalance', 'importance': 0.10},
                    {'feature': 'order_flow', 'importance': 0.09},
                    {'feature': 'trend_strength_15m', 'importance': 0.08},
                    {'feature': 'fvg_score', 'importance': 0.07},
                    {'feature': 'liquidity_sweep', 'importance': 0.06},
                    {'feature': 'smc_signal', 'importance': 0.05},
                    {'feature': 'volume_spike', 'importance': 0.04},
                    {'feature': 'volatility_15m', 'importance': 0.03}
                ]
            })
    
    except Exception as e:
        logger.error(f"Error loading SHAP data: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/shap/plot', methods=['GET'])
@token_required
def get_shap_plot(current_user_email):
    """Serve SHAP feature importance plot."""
    try:
        project_root = Path(__file__).parent.parent.parent
        plot_file = project_root / 'reports' / 'shap_plots' / 'feature_importance.png'
        
        if plot_file.exists():
            return send_file(plot_file, mimetype='image/png')
        else:
            return jsonify({'error': 'SHAP plot not found'}), 404
    
    except Exception as e:
        logger.error(f"Error serving SHAP plot: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/config', methods=['GET', 'POST'])
@token_required
@limiter.limit("30 per minute")  # FIXED: Add rate limiting
def manage_config(current_user_email):
    """Get or update application configuration.
    
    GET: Returns current configuration
    POST: Updates configuration (body: JSON config object)
    """
    project_root = Path(__file__).parent.parent.parent
    config_file = project_root / 'config' / 'user_config.json'
    
    if request.method == 'GET':
        try:
            # Return default config if file doesn't exist
            if not config_file.exists():
                default_config = {
                    'model': {
                        'asset': 'gold',
                        'timeframe': '15m',
                        'session_filter': True
                    },
                    'backtest': {
                        'initial_capital': 10000,
                        'risk_per_trade': 100,
                        'commission_pct': 0.0001,
                        'slippage_pct': 0.0002
                    },
                    'notifications': {
                        'enabled': False,
                        'email': '',
                        'signal_threshold': 0.7
                    },
                    'display': {
                        'theme': 'light',
                        'chart_style': 'candlestick',
                        'show_indicators': True
                    }
                }
                return jsonify(default_config)
            
            # Load existing config
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            return jsonify(config)
        
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            new_config = request.json
            
            if not new_config:
                return jsonify({'error': 'No configuration provided'}), 400
            
            # Create config directory if it doesn't exist
            config_file.parent.mkdir(exist_ok=True)
            
            # Save configuration
            with open(config_file, 'w') as f:
                json.dump(new_config, f, indent=2)
            
            logger.info("Configuration updated successfully")
            
            return jsonify({
                'message': 'Configuration updated successfully',
                'config': new_config
            })
        
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return jsonify({'error': str(e)}), 500


@app.route('/api/models/info', methods=['GET'])
@token_required
@limiter.limit("60 per minute")  # FIXED: Add rate limiting
def get_model_info(current_user_email):
    """Get model metadata and information.
    
    Query params:
        asset: Asset to get model info for (gold or silver, default: gold)
    """
    try:
        asset = request.args.get('asset', 'gold').lower()
        
        # Validate asset
        if asset not in ['gold', 'silver']:
            return jsonify({'error': 'Invalid asset. Must be "gold" or "silver"'}), 400
        
        # FIXED: Use ModelManager for lazy loading
        model, feature_names = model_manager.get_or_load_model(asset)
        if model is None:
            return jsonify({'error': f'Model not found for {asset}'}), 404
        
        # Get model file path for metadata
        if asset == "gold":
            model_path = MODELS_DIR / 'enhanced_15m.pkl'
        else:
            model_path = MODELS_DIR / 'processed' / 'silver_model_enhanced.pkl'
        
        # Get file modification time
        import os
        from datetime import datetime
        if model_path.exists():
            mtime = os.path.getmtime(model_path)
            last_updated = datetime.fromtimestamp(mtime).isoformat()
            file_size_mb = os.path.getsize(model_path) / (1024 * 1024)
        else:
            last_updated = 'unknown'
            file_size_mb = 0
        
        # Build response
        info = {
            'asset': asset,
            'model_type': 'XGBoost Classifier',
            'version': '1.0',
            'last_updated': last_updated,
            'file_size_mb': round(file_size_mb, 2),
            'features_count': len(feature_names) if feature_names else 'unknown',
            'timeframe': '15m',
            'session_filter': 'London + NY (08:00-17:00)',
            'training_config': {
                'primary_timeframe': '15m',
                'multi_timeframe': ['5m', '30m', '1h'],
                'features': ['Volume', 'SMC', 'Multi-timeframe']
            }
        }
        
        # Add feature names if requested
        if request.args.get('include_features') == 'true' and feature_names:
            info['feature_names'] = feature_names[:50]  # Limit to first 50
            info['total_features'] = len(feature_names)
        
        return jsonify(info)
    
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        return jsonify({'error': str(e)}), 500


# REMOVED: Flask UI serving routes - now using Next.js frontend
# All UI routes removed to make Flask API-only

# WebSocket event handlers for real-time features
@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    logger.info('Client connected')
    emit('connected', {'status': 'success'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    logger.info('Client disconnected')

@socketio.on('subscribe_predictions')
def handle_subscribe_predictions(data):
    """Subscribe to real-time prediction updates."""
    logger.info(f'Client subscribed to predictions: {data}')
    emit('subscription_confirmed', {'type': 'predictions'})

@socketio.on('subscribe_etl_status')
def handle_subscribe_etl_status(data):
    """Subscribe to ETL pipeline status updates."""
    logger.info(f'Client subscribed to ETL status: {data}')
    emit('subscription_confirmed', {'type': 'etl_status'})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
