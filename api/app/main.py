"""
Flask API for ML Signals Dashboard
Serves predictions, backtest results, and SHAP explainability data.
"""

import os
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_compress import Compress  # FIXED: Add compression
from flask_socketio import SocketIO, emit
from werkzeug.middleware.proxy_fix import ProxyFix
import pickle
import pandas as pd
import json  # FIXED: Removed duplicate import
from pathlib import Path
import logging
import sys
from functools import lru_cache
from datetime import datetime, timedelta, timezone
import threading
import time
from typing import Dict, Any
import numpy as np

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False

# Load environment variables from .env if present
load_dotenv()


def _validate_secrets():
    """Reject startup if critical secrets are still placeholder values."""
    placeholders = {
        'SECRET_KEY': {'your-flask-secret-key-here', 'replace-with-a-strong-random-secret-key', ''},
        'JWT_SECRET_KEY': {'replace-with-a-strong-random-jwt-key', ''},
        'REFRESH_SECRET_KEY': {'replace-with-a-strong-random-refresh-key', ''},
    }
    # FLASK_SECRET_KEY is an accepted alias for SECRET_KEY (used by security_service)
    aliases = {'SECRET_KEY': 'FLASK_SECRET_KEY'}
    errors = []
    for key, bad_values in placeholders.items():
        alias = aliases.get(key)
        val = os.environ.get(key, '') or (os.environ.get(alias, '') if alias else '')
        if val in bad_values:
            errors.append(f"  {key} is set to a placeholder — generate a real value")
    if errors:
        logging.basicConfig(level=logging.CRITICAL)
        logging.critical("SECRET VALIDATION FAILED — refusing to start:\n" + "\n".join(errors))
        sys.exit(1)


# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data.loaders import load_gold_data, load_silver_data, load_asset_data
from features.pipeline import engineer_all_features

# Import extensions, database and authentication
from api.app.extensions import limiter, migrate
from api.app.database import init_database, db
from api.app.auth import init_auth, token_required
from api.app.watchlist import watchlist_bp
from api.app.profile import profile_bp
from api.app.middleware.error_handler import register_error_handlers
from api.app.etl_routes import etl_bp
from api.app.pipeline_routes import pipeline_bp
from api.app.memory_routes import memory_bp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_validate_secrets()

app = Flask(__name__)

# WSGI middleware: handle CORS for ALL paths including /socket.io
ALLOWED_ORIGINS = {"http://localhost:3000", "http://127.0.0.1:3000"}
_extra_origins = os.environ.get('CORS_ORIGINS', '')
if _extra_origins:
    ALLOWED_ORIGINS.update(o.strip() for o in _extra_origins.split(',') if o.strip())

class CORSProxy:
    """Wraps every response with CORS headers — sits above engine.io."""
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        origin = environ.get('HTTP_ORIGIN', '')
        method = environ.get('REQUEST_METHOD', '')

        if origin in ALLOWED_ORIGINS:
            def add_cors(status, headers, exc_info=None):
                headers = list(headers)
                header_names = {h[0].lower() for h in headers}
                if 'access-control-allow-origin' not in header_names:
                    headers.append(('Access-Control-Allow-Origin', origin))
                if 'access-control-allow-credentials' not in header_names:
                    headers.append(('Access-Control-Allow-Credentials', 'true'))
                if method == 'OPTIONS':
                    headers.append(('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS'))
                    headers.append(('Access-Control-Allow-Headers', 'Content-Type, Authorization'))
                    headers.append(('Access-Control-Max-Age', '86400'))
                return start_response(status, headers, exc_info)

            if method == 'OPTIONS' and environ.get('PATH_INFO', '').startswith('/socket.io'):
                response_body = b''
                start_response('204 No Content', [
                    ('Content-Type', 'text/plain'),
                    ('Content-Length', '0'),
                    ('Access-Control-Allow-Origin', origin),
                    ('Access-Control-Allow-Credentials', 'true'),
                    ('Access-Control-Allow-Methods', 'GET, POST, OPTIONS'),
                    ('Access-Control-Allow-Headers', 'Content-Type'),
                    ('Access-Control-Max-Age', '86400'),
                ])
                return [response_body]

            return self.app(environ, add_cors)

        return self.app(environ, start_response)

# Apply ProxyFix first
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Initialize SocketIO for real-time features
socketio = SocketIO(
    app,
    cors_allowed_origins=ALLOWED_ORIGINS,
    async_mode='threading',
    logger=False,
    engineio_logger=False,
    ping_timeout=20,
    ping_interval=25,
)

# CRITICAL: Apply CORSProxy AFTER socketio wraps wsgi_app
# This ensures CORS headers are added to ALL responses including /socket.io
app.wsgi_app = CORSProxy(app.wsgi_app)

# Global state for real-time features
connected_clients: Dict[str, Dict[str, Any]] = {}
prediction_thread = None
thread_running = False

# FIXED: Register centralized error handlers
register_error_handlers(app)


@app.after_request
def set_security_headers(response):
    """Add security headers and CORS to every response."""
    origin = request.headers.get('Origin', '')
    
    # CORS for API routes
    if request.path.startswith('/api') or request.path.startswith('/auth'):
        if origin in ALLOWED_ORIGINS:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            response.headers['Access-Control-Expose-Headers'] = 'Content-Type, Authorization'
    
    # Content Security Policy — restrict resource loading to known safe origins
    # For development: allow localhost connections. For production: restrict to your domain.
    env = app.config.get('ENV', 'production')
    if env == 'development':
        connect_src = "connect-src 'self' http://localhost:* ws://localhost:*; "
    else:
        connect_src = "connect-src 'self' *; "
    
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://s.tradingview.com https://unpkg.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.tailwindcss.com https://cdnjs.cloudflare.com; "
        "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
        "img-src 'self' data: https:; "
        f"{connect_src}"
        "frame-src https://www.tradingview.com https://s.tradingview.com; "
        "frame-ancestors 'self';"
    )
    # Prevent clickjacking (allow TradingView iframe)
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
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

# CORS handled by flask-socketio for /socket.io and after_request for /api
# Do NOT use flask-cors — it conflicts with engine.io's CORS handling

# FIXED: Enable response compression for all endpoints
Compress(app)

# FIXED: Initialize extensions correctly for modern Flask (v3.0+)
limiter.init_app(app)

# Limit request body size — 2MB max (prevents DoS via large payloads)
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

# Initialize database FIRST (auth depends on it)
init_database(app)

# Initialize Flask-Migrate
migrate.init_app(app, db)

# Initialize authentication
init_auth(app)

# Register additional blueprints
app.register_blueprint(watchlist_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(etl_bp)
app.register_blueprint(pipeline_bp)
app.register_blueprint(memory_bp)


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
        """Load model for specific asset. V4 for gold, enhanced for silver."""
        if asset == "gold":
            model_path = self.models_dir / 'gold_regression_system.pkl'
        elif asset == "silver":
            model_path = self.models_dir / 'silver_enhanced_15m.pkl'
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
                    # V4 format: {direction_model, tp_model, sl_model, features}
                    if 'direction_model' in model_data:
                        model = model_data['direction_model']
                        feature_names = model_data.get('features', None)
                    else:
                        model = model_data['model']
                        feature_names = model_data.get('features', None)
                else:
                    model = model_data
                    try:
                        feature_names = list(model.feature_names_in_) if hasattr(model, 'feature_names_in_') else None
                    except (AttributeError, Exception):
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
                if (datetime.now(timezone.utc) - cache_time).total_seconds() < self._ttl:
                    return data
        return None
    
    def set(self, key: str, data):
        """Set cached data with current timestamp."""
        with self._lock:
            self._cache[key] = (data, datetime.now(timezone.utc))
    
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
                age = (datetime.now(timezone.utc) - cache_time).total_seconds()
                if age < self._ttl and current_mtime == cached_mtime:
                    return data
            
            # Cache miss or expired - load file
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                self._cache[cache_key] = (data, datetime.now(timezone.utc), current_mtime)
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
        self._status = {'running': False, 'progress': 0, 'error': None, 'result': None}
    
    def is_running(self) -> bool:
        with self._lock:
            return self._status['running']

    def get_status(self) -> dict:
        with self._lock:
            return self._status.copy()

    def run(self, start_date: str, end_date: str, asset: str = 'gold') -> dict:
        with self._lock:
            if self._status['running']:
                return {'error': 'Backtest already running', 'status': self._status}, 409
            self._status = {'running': True, 'progress': 0, 'error': None, 'result': None}

        def _run_backtest():
            try:
                import pandas as pd
                import numpy as np
                from config.settings import REPORTS_DIR
                from data.loaders import load_asset_data
                from features.pipeline import engineer_all_features

                with self._lock:
                    self._status['progress'] = 10

                # Load data using the same loader as predictions
                df = load_asset_data(asset=asset, primary_tf='15m', session_filter=False)
                if df is None or len(df) < 50:
                    with self._lock:
                        self._status = {'running': False, 'progress': 0, 'error': 'Insufficient data loaded', 'result': None}
                    return

                # Filter by date range
                df = df[start_date:end_date]
                if len(df) < 50:
                    with self._lock:
                        self._status = {'running': False, 'progress': 0, 'error': f'Insufficient data for date range: {len(df)} bars', 'result': None}
                    return

                with self._lock:
                    self._status['progress'] = 30

                # Engineer features
                featured_df = engineer_all_features(df, add_labels=False)

                # Apply V4-specific features
                from features.v4_features import compute_v4_features
                featured_df = compute_v4_features(featured_df)

                with self._lock:
                    self._status['progress'] = 40

                # Load model with feature names
                model, feature_names = model_manager.get_or_load_model(asset)
                if model is None:
                    with self._lock:
                        self._status = {'running': False, 'progress': 0, 'error': f'Model not found for {asset}', 'result': None}
                    return

                # Align features with model expectations (same logic as predictions)
                X_input = featured_df.copy()
                if feature_names is not None:
                    current_cols = X_input.columns
                    col_lookup = {}
                    for col in current_cols:
                        norm = col.lower().replace('_', '')
                        col_lookup[norm] = col
                        if norm == 'sessionasia': col_lookup['asia'] = col
                        if norm == 'sessionlondon' or norm == 'sessionldn': col_lookup['ldn'] = col
                        if norm == 'sessionny': col_lookup['ny'] = col

                    rename_map = {}
                    for feat in feature_names:
                        if feat in current_cols: continue
                        feat_norm = feat.lower().replace('_', '')
                        if feat_norm in col_lookup:
                            rename_map[col_lookup[feat_norm]] = feat

                    if rename_map:
                        X_input.rename(columns=rename_map, inplace=True)

                    try:
                        X = X_input[feature_names]
                    except KeyError:
                        available = [f for f in feature_names if f in X_input.columns]
                        X = X_input[available]
                else:
                    X = X_input.select_dtypes(include=['float64', 'int64']).fillna(0)

                with self._lock:
                    self._status['progress'] = 60

                # Predict signals with V4 trend filter
                raw_predictions = model.predict(X)
                try:
                    raw_probas = model.predict_proba(X)[:, 1]
                except (AttributeError, IndexError):
                    raw_probas = np.full(len(raw_predictions), 0.5)

                signals = np.zeros(len(raw_predictions), dtype=int)
                if 'trend_ema_cross' in X.columns:
                    for i in range(len(raw_predictions)):
                        proba = raw_probas[i]
                        trend = X.iloc[i].get('trend_ema_cross', 0)
                        confidence = max(proba, 1 - proba)
                        if trend == 1 and proba >= 0.5 and confidence >= 0.65:
                            signals[i] = 1   # BUY
                        elif trend == 0 and proba < 0.5 and confidence >= 0.65:
                            signals[i] = -1  # SELL
                else:
                    signals = (np.array(raw_predictions) > 0).astype(int)

                with self._lock:
                    self._status['progress'] = 75

                # Run backtest engine
                from backtesting.engine import BacktestEngine
                engine = BacktestEngine(asset=asset)
                results = engine.run_backtest(featured_df, signals)

                with self._lock:
                    self._status['progress'] = 90

                # Build response
                metrics = results.get('metrics', {})
                trades_list = []
                for t in results.get('trades', []):
                    trades_list.append({
                        'entry_time': t.entry_time.isoformat() if hasattr(t, 'entry_time') else str(t.get('entry_time', '')),
                        'exit_time': t.exit_time.isoformat() if hasattr(t, 'exit_time') else str(t.get('exit_time', '')),
                        'entry_price': t.entry_price if hasattr(t, 'entry_price') else t.get('entry_price', 0),
                        'exit_price': t.exit_price if hasattr(t, 'exit_price') else t.get('exit_price', 0),
                        'pnl_pct': t.pnl_pct if hasattr(t, 'pnl_pct') else t.get('pnl_pct', 0),
                        'pnl_usd': t.pnl_usd if hasattr(t, 'pnl_usd') else t.get('pnl_usd', 0),
                        'hit_tp': t.hit_tp if hasattr(t, 'hit_tp') else t.get('hit_tp', False),
                        'hit_sl': t.hit_sl if hasattr(t, 'hit_sl') else t.get('hit_sl', False),
                    })

                pf = metrics.get('profit_factor', 0)
                if not np.isfinite(pf):
                    pf = 0

                response = {
                    'win_rate': metrics.get('win_rate', 0),
                    'profit_factor': pf,
                    'max_drawdown': metrics.get('max_drawdown_pct', 0),
                    'total_trades': metrics.get('n_trades', 0),
                    'net_profit': metrics.get('total_return_usd', 0),
                    'sharpe_ratio': metrics.get('sharpe_ratio', 0),
                    'sortino_ratio': metrics.get('sortino_ratio', 0),
                    'calmar_ratio': metrics.get('calmar_ratio', 0),
                    'trades': trades_list,
                    'asset': asset,
                }

                with self._lock:
                    self._status = {
                        'running': False, 'progress': 100, 'error': None,
                        'result': response
                    }

            except Exception as e:
                logger.error(f"Backtest failed: {e}")
                import traceback
                traceback.print_exc()
                with self._lock:
                    self._status = {'running': False, 'progress': 0, 'error': str(e), 'result': None}

        thread = threading.Thread(target=_run_backtest, daemon=True)
        thread.start()

        return {'status': 'started', 'message': 'Backtest started'}, 202


# FIXED: Initialize managers (no global dicts!)
model_manager = ModelManager()
prediction_cache = PredictionCache(ttl_seconds=300)
backtest_manager = BacktestManager()
file_cache = FileCache(ttl_seconds=60)  # FIXED: Cache for JSON files

# Initialize prediction logger and email alerts
from etl.prediction_logger import PredictionLogger
from etl.alerts import EmailAlertService
from etl.guards.alert_risk_gate import AlertRiskGate
from etl.agents.llm_client import NemotronClient
from etl.agents.signal_reasoner import SignalReasoner

prediction_logger = PredictionLogger()
from etl.prediction_logger import ActiveTradeTracker
active_trades = ActiveTradeTracker()
email_alerts = EmailAlertService(confidence_threshold=0.70)
# Deterministic gate — runs unconditionally on every candidate alert.
alert_risk_gate = AlertRiskGate()

# Initialize signal memory pipeline (ChromaDB + confidence adjustment)
from signal_memory.client import SignalMemoryClient
from signal_memory.retriever import SignalRetriever
from signal_memory.updater import SignalUpdater
from self_learning.tracker import OutcomeTracker

signal_client = SignalMemoryClient()
signal_retriever = SignalRetriever(client=signal_client)
signal_updater = SignalUpdater(client=signal_client)
outcome_tracker = OutcomeTracker()
# LLM agent — off by default (ML_AGENT_ENABLED). Fail-open. Backtest path never imports this.
signal_reasoner = SignalReasoner(client=NemotronClient(), pred_logger=prediction_logger)

logger.info("✅ Server ready - models will be loaded on first request (lazy loading)")
logger.info("✅ ModelManager, PredictionCache, BacktestManager, PredictionLogger initialized")


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


@app.route('/api/market/price', methods=['GET'])
@limiter.limit("30 per minute")
def get_live_price():
    """Fetch real-time price from MT5 cache (written by mt5_price_cache.py on host).
    Returns 503 if cache is missing or stale (>60s old).
    
    Query params:
        asset: gold or silver (default: gold)
    """
    try:
        asset = request.args.get('asset', 'gold').lower()
        
        if asset not in ['gold', 'silver']:
            return jsonify({'error': 'Invalid asset. Must be "gold" or "silver"'}), 400
        
        # Read MT5 cache
        cache_path = Path(__file__).parent.parent.parent / 'data' / 'mt5_prices.json'
        if not cache_path.exists():
            return jsonify({'error': 'MT5 price cache not found. Run mt5_price_cache.py on host.', 'source': 'none'}), 503
        
        try:
            with open(cache_path, encoding='utf-8-sig') as f:
                cache = json.load(f)
            
            updated_at = datetime.fromisoformat(cache['updated_at'])
            age_seconds = (datetime.now() - updated_at).total_seconds()
            
            if age_seconds > 60:
                return jsonify({'error': f'MT5 cache stale ({int(age_seconds)}s old). Check mt5_price_cache.py.', 'source': 'stale'}), 503
            
            if asset not in cache.get('prices', {}):
                return jsonify({'error': f'No MT5 price data for {asset}'}), 404
            
            price_data = cache['prices'][asset]
            return jsonify({
                'asset': asset,
                'price': price_data['price'],
                'bid': price_data.get('bid'),
                'ask': price_data.get('ask'),
                'spread': price_data.get('spread'),
                'source': 'mt5',
                'timestamp': price_data['timestamp'],
            })
        except (json.JSONDecodeError, KeyError, ValueError):
            return jsonify({'error': 'MT5 cache file corrupted'}), 500
    
    except Exception as e:
        logger.error(f"Error fetching live price: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/predictions/latest', methods=['GET'])
@limiter.limit("100 per minute")  # FIXED: Add rate limiting
def get_latest_predictions():
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
            # load_asset_data returns multi-TF aligned data (15m + 30m + 1h columns)
            df = load_asset_data(asset=asset, primary_tf='15m', session_filter=False)

            # Apply standard feature engineering
            df = engineer_all_features(df, add_labels=False)

            # Cache the engineered data (without V4 features)
            prediction_cache.set(cache_key, df)
        else:
            logger.info(f"Using cached data for {asset}")
        
        # Work on a COPY to avoid corrupting the cached dataframe
        df = df.copy()
        
        # Always compute V4 features (they depend on live data)
        from features.v4_features import compute_v4_features
        df = compute_v4_features(df)
        
        # Inject current live price from MT5 cache into the latest bar
        try:
            cache_path = Path(__file__).parent.parent.parent / 'data' / 'mt5_prices.json'
            if cache_path.exists():
                with open(cache_path, encoding='utf-8-sig') as f:
                    cache = json.load(f)
                if asset in cache.get('prices', {}):
                    live_price = cache['prices'][asset]['price']
                    latest_idx = df.index[-1]
                    df.loc[latest_idx, 'close'] = live_price
                    df.loc[latest_idx, 'open'] = live_price
                    df.loc[latest_idx, 'high'] = live_price
                    df.loc[latest_idx, 'low'] = live_price
                    df.loc[latest_idx, 'price'] = live_price
                    logger.info(f"Injected MT5 live price ${live_price:.2f} into latest {asset} bar")
        except Exception as e:
            logger.warning(f"Could not load MT5 live price: {e}")
        
        # Get most recent N bars
        recent_data = df.iloc[-limit:].copy()
        
        # FIXED: Robustly align column names with model expectations
        # Use a copy for prediction to avoid breaking the response preparation
        X_input = recent_data.copy()
        
        if feature_names is not None:
            # Create a normalized mapping for current columns
            current_cols = X_input.columns
            col_lookup = {}
            for col in current_cols:
                norm = col.lower().replace('_', '')
                col_lookup[norm] = col
                if norm == 'sessionasia': col_lookup['asia'] = col
                if norm == 'sessionlondon' or norm == 'sessionldn': col_lookup['ldn'] = col
                if norm == 'sessionny': col_lookup['ny'] = col
            
            rename_map = {}
            for feat in feature_names:
                if feat in current_cols: continue
                feat_norm = feat.lower().replace('_', '')
                if feat_norm in col_lookup:
                    rename_map[col_lookup[feat_norm]] = feat
            
            if rename_map:
                logger.info(f"Mapping {len(rename_map)} features for prediction")
                X_input.rename(columns=rename_map, inplace=True)
            
            try:
                # Reorder and select only needed features
                X = X_input[feature_names]
            except KeyError as e:
                logger.error(f"❌ Final alignment failed. Missing: {e}")
                available_features = [f for f in feature_names if f in X_input.columns]
                X = X_input[available_features]
        else:
            X = X_input.select_dtypes(include=['float64', 'int64'])
        
        # Get predictions and probabilities
        predictions = model.predict(X)

        try:
            probabilities = model.predict_proba(X)[:, 1]
        except (AttributeError, IndexError):
            probabilities = [0.5] * len(predictions)

        # V4 trend filter: BUY when trend_ema_cross==1 AND proba>=0.5 AND confidence>=0.65
        # SELL when trend_ema_cross==0 AND proba<0.5 AND confidence>=0.65
        # HOLD otherwise
        if 'trend_ema_cross' in X.columns:
            for i in range(len(predictions)):
                proba = probabilities[i]
                trend = X.iloc[i].get('trend_ema_cross', 0)
                confidence = max(proba, 1 - proba)
                if trend == 1 and proba >= 0.5 and confidence >= 0.65:
                    predictions[i] = 1   # BUY
                elif trend == 0 and proba < 0.5 and confidence >= 0.65:
                    predictions[i] = -1  # SELL
                else:
                    predictions[i] = 0   # HOLD
        
        # Compute real SHAP values for the latest bar
        default_shap = [{'feature': 'N/A', 'contribution': 0.0}]
        shap_values_for_response = [default_shap] * len(predictions)
        try:
            if SHAP_AVAILABLE and len(X) > 0:
                # Try to create explainer - handle different model types
                try:
                    explainer = shap.TreeExplainer(model)
                except Exception:
                    # Fallback for models that don't support TreeExplainer
                    logger.warning("TreeExplainer failed, trying KernelExplainer")
                    explainer = shap.KernelExplainer(model.predict, shap.sample(X, 100))
                
                latest_bar = X.iloc[[-1]]
                shap_vals = explainer.shap_values(latest_bar)
                
                # Handle different SHAP output formats
                if isinstance(shap_vals, list):
                    shap_vals = shap_vals[1]  # Binary classification - use positive class
                if isinstance(shap_vals, np.ndarray) and shap_vals.ndim > 1:
                    shap_vals = shap_vals[0]
                
                # Get top 5 features by absolute SHAP value
                top_idx = np.argsort(np.abs(shap_vals))[::-1][:5]
                top_shap = [
                    {'feature': X.columns[j], 'contribution': float(shap_vals[j])}
                    for j in top_idx
                ]
                
                # Assign to all bars (same model, same features)
                shap_values_for_response = [top_shap] * len(predictions)
                logger.info(f"✅ SHAP computed: {len(top_shap)} features")
        except Exception as e:
            logger.warning(f"SHAP computation failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Prepare response
        tp_pct = 0.0045 if asset == 'gold' else 0.003
        sl_pct = 0.0015 if asset == 'gold' else 0.001

        # ── Active trade: freeze TP/SL instead of recalculating ──
        active = active_trades.get_active(asset)
        frozen_tp = active['tp_price'] if active else None
        frozen_sl = active['sl_price'] if active else None
        frozen_signal = active['signal'] if active else None

        results = []
        for i, (idx, row) in enumerate(recent_data.iterrows()):
            bar_shap = shap_values_for_response[-1] if i == len(recent_data) - 1 else shap_values_for_response[0]
            entry_price = float(row['close'])
            signal_val = int(predictions[i])
            prob_val = float(probabilities[i])

            # If there's an active trade, lock the signal and TP/SL
            if active and i == len(recent_data) - 1:  # Only override the latest bar
                signal_val = frozen_signal
                tp_price = frozen_tp
                sl_price = frozen_sl
            else:
                tp_price = round(entry_price * (1 + tp_pct), 2)
                sl_price = round(entry_price * (1 - sl_pct), 2)

            results.append({
                'timestamp': idx.isoformat(),
                'asset': asset.upper(),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'price': float(row['close']),
                'signal': signal_val,
                'probability': prob_val,
                'confidence': prob_val,
                'tp_price': tp_price,
                'sl_price': sl_price,
                'shap_values': bar_shap,
                'trade_active': active is not None,  # Frontend can show "TRADE ACTIVE"
            })

        # Log prediction and manage active trades
        if results:
            latest = results[-1]
            entry_price = latest['price']
            is_buy_sell = latest['signal'] in (1, -1)
            high_confidence = latest['confidence'] > 0.65

            if is_buy_sell and high_confidence:
                if not active_trades.has_active(asset):
                    # Open new trade with FROZEN TP/SL
                    tp_price = round(entry_price * (1 + tp_pct), 2)
                    sl_price = round(entry_price * (1 - sl_pct), 2)
                    active_trades.open_trade(
                        asset=asset,
                        signal=int(latest['signal']),
                        confidence=latest['confidence'],
                        entry_price=entry_price,
                        tp_price=tp_price,
                        sl_price=sl_price,
                        shap_values=latest.get('shap_values', []),
                    )
                    # Override latest result with frozen values
                    latest['tp_price'] = tp_price
                    latest['sl_price'] = sl_price
                    latest['trade_active'] = True

                    prediction_logger.log_prediction(
                        asset=asset,
                        signal=latest['signal'],
                        confidence=latest['confidence'],
                        price=latest['price'],
                        shap_values=latest.get('shap_values', []),
                        tp_price=tp_price,
                        sl_price=sl_price,
                    )
            elif not is_buy_sell:
                # HOLD signal — only log if no active trade
                if not active_trades.has_active(asset):
                    prediction_logger.log_prediction(
                        asset=asset,
                        signal=latest['signal'],
                        confidence=latest['confidence'],
                        price=latest['price'],
                        shap_values=latest.get('shap_values', []),
                        tp_price=round(entry_price * (1 + tp_pct), 2),
                        sl_price=round(entry_price * (1 - sl_pct), 2),
                    )
            
            # Store signal in ChromaDB for similarity search
            try:
                signal_features = {
                    'asset': asset,
                    'signal': int(latest['signal']),
                    'confidence': float(latest['confidence']),
                    'price': float(latest['price']),
                }
                # Add key SHAP features for embedding (ensure list type)
                shap_raw = latest.get('shap_values', [])
                if isinstance(shap_raw, list):
                    for shap_item in shap_raw[:5]:
                        if isinstance(shap_item, dict):
                            signal_features[str(shap_item.get('feature', 'unknown'))] = float(shap_item.get('contribution', 0))
                
                signal_updater.store_signal(signal_features)
            except Exception as e:
                logger.warning(f"Could not store signal in ChromaDB: {e}")
            
            # Adjust confidence based on similar past signals
            try:
                base_confidence = latest['confidence']
                adjusted_confidence = signal_retriever.adjust_confidence(
                    signal_features, base_confidence
                )
                if adjusted_confidence != base_confidence:
                    logger.info(f"Confidence adjusted: {base_confidence:.3f} → {adjusted_confidence:.3f}")
                    latest['confidence'] = adjusted_confidence
            except Exception as e:
                logger.warning(f"Could not adjust confidence: {e}")
            
            # Send email alert if confidence > 70% and signal is BUY/SELL
            if email_alerts.should_alert(latest['signal'], latest['confidence']):
                # Pull live indicator values for the gates/agent. These columns are
                # produced by features/pipeline.engineer_all_features; guard with .get
                # so a missing column never breaks the alert path.
                last_row = recent_data.iloc[-1]

                def _col(name, default=0.0):
                    v = getattr(last_row, name, None) if hasattr(last_row, name) else last_row.get(name) if hasattr(last_row, 'get') else None
                    try:
                        return float(v) if v is not None and v == v else default
                    except (TypeError, ValueError):
                        return default

                rsi = _col('rsi_14', _col('rsi', 50.0))
                atr = _col('atr_14', _col('atr', 0.0))
                ema20 = _col('ema_20', latest['price'])
                ema50 = _col('ema_50', latest['price'])

                # 1. Deterministic gate (always runs) — cooldown, session, volatility.
                risk = alert_risk_gate.check(
                    asset=asset, price=latest['price'], atr=atr,
                    signal=latest['signal'], confidence=latest['confidence'],
                )
                if not risk.approved:
                    logger.info(f"Alert suppressed by risk gate: {risk.reason}")
                else:
                    # 2. LLM agent gate (off by default, fail-open). Optional refinement.
                    agent = signal_reasoner.evaluate(
                        asset=asset, signal=latest['signal'],
                        confidence=latest['confidence'], rsi=rsi, atr=atr,
                        ema20=ema20, ema50=ema50, price=latest['price'],
                    )
                    if agent.source == "llm":
                        logger.info(f"Agent decision: approved={agent.approved} ({agent.reason})")
                    if agent.approved:
                        email_alerts.send_alert(
                            asset=asset,
                            signal=latest['signal'],
                            confidence=latest['confidence'],
                            price=latest['price'],
                            shap_values=latest.get('shap_values', [])
                        )
                    else:
                        logger.info(f"Alert suppressed by agent: {agent.reason}")
        
        # Check outcomes for all assets using current prices
        try:
            live_prices = {}
            for a in ['gold', 'silver']:
                cache_path = Path(__file__).parent.parent.parent / 'data' / 'mt5_prices.json'
                if cache_path.exists():
                    with open(cache_path, encoding='utf-8-sig') as f:
                        cache = json.load(f)
                    if a in cache.get('prices', {}):
                        live_prices[a] = cache['prices'][a]['price']

            # ── Check active trades first ──
            for a in ['gold', 'silver']:
                if a in live_prices and active_trades.has_active(a):
                    resolved = active_trades.check_outcome(a, live_prices[a])
                    if resolved:
                        # Trade resolved — log outcome and update tracker
                        outcome_tracker.log_outcome(
                            signal_id=f"{resolved['opened_at']}_{a}",
                            asset=a,
                            signal=resolved['signal'],
                            confidence=resolved['confidence'],
                            price=resolved['close_price'],
                            entry_price=resolved['entry_price'],
                            outcome=resolved['outcome'],
                            pnl=resolved['actual_pnl'],
                        )

            # Also run legacy outcome check for non-trade-tracked predictions
            if live_prices:
                prediction_logger.check_outcomes(live_prices)

                # Update outcome tracker for self-learning
                try:
                    for log_file in sorted(Path('/app/reports/predictions').glob('predictions_*.jsonl'))[-3:]:
                        for line in log_file.read_text().splitlines():
                            record = json.loads(line)
                            if record.get('actual_outcome') and record.get('signal') != 0:
                                outcome_tracker.log_outcome(
                                    signal_id=f"{record['timestamp']}_{record['asset']}",
                                    asset=record['asset'],
                                    signal=record['signal'],
                                    confidence=record['confidence'],
                                    price=record.get('price', 0),
                                    entry_price=record.get('price', 0),
                                    outcome=record['actual_outcome'],
                                    pnl=record.get('actual_pnl', 0),
                                )
                except Exception as e:
                    logger.warning(f"Could not update outcome tracker: {e}")
            
            # Check if retraining is needed (daily, not on every request)
            try:
                from self_learning.retrainer import ModelRetrainer
                retrainer = ModelRetrainer()
                if retrainer.should_retrain(min_outcomes=10, accuracy_threshold=0.55):
                    logger.info("Retrain triggered — running in background")
                    import threading
                    threading.Thread(
                        target=retrainer.retrain_model,
                        args=(asset,),
                        daemon=True
                    ).start()
            except Exception as e:
                logger.warning(f"Retrain check failed: {e}")
        except Exception as e:
            logger.warning(f"Could not check outcomes: {e}")

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


@app.route('/api/predictions/history', methods=['GET'])
@limiter.limit("30 per minute")
def get_prediction_history():
    """Get prediction log history for the trade log page.

    Query params:
        days: Number of days to look back (default 7)
        asset: Filter by asset (gold/silver, optional)
        limit: Max records to return (default 200)
    """
    try:
        days = int(request.args.get('days', 7))
        asset = request.args.get('asset', '').strip() or None
        limit = int(request.args.get('limit', 200))

        days = max(1, min(days, 90))
        limit = max(1, min(limit, 1000))

        # Get all records first (no limit), then filter, then apply limit
        history = prediction_logger.get_history(days=days, asset=asset, limit=10000)
        # Filter out HOLD signals — only show actionable trades (BUY/SELL)
        history = [r for r in history if r.get('signal') != 0]
        
        # Sort by timestamp descending (newest first)
        history.sort(key=lambda r: r.get('timestamp', ''), reverse=True)
        
        # Apply limit after filtering
        history = history[:limit]
        
        summary = prediction_logger.get_summary(days=days)

        return jsonify({
            'predictions': history,
            'summary': summary,
        }), 200

    except Exception as e:
        logger.error(f"Error getting prediction history: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/orchestrator/status', methods=['GET'])
@limiter.limit("30 per minute")
def get_orchestrator_status():
    """Get full orchestrator status for the dashboard."""
    try:
        from etl.orchestrator import PipelineOrchestrator
        orch = PipelineOrchestrator()
        
        # MT5 cache status
        cache_path = Path(__file__).parent.parent.parent / 'data' / 'mt5_prices.json'
        mt5_status = {'exists': False, 'fresh': False, 'age_seconds': None}
        if cache_path.exists():
            try:
                with open(cache_path, encoding='utf-8-sig') as f:
                    cache = json.load(f)
                updated_at = datetime.fromisoformat(cache['updated_at'])
                age = (datetime.now() - updated_at).total_seconds()
                mt5_status = {
                    'exists': True,
                    'fresh': age < 60,
                    'age_seconds': round(age),
                    'updated_at': cache['updated_at'],
                }
            except Exception:
                mt5_status = {'exists': True, 'fresh': False, 'age_seconds': None, 'error': 'parse failed'}
        
        # ChromaDB status
        chroma_status = {'connected': False, 'signal_count': 0}
        try:
            from signal_memory.client import SignalMemoryClient
            client = SignalMemoryClient()
            collection = client.get_collection('signal_patterns')
            chroma_status = {'connected': True, 'signal_count': collection.count()}
        except Exception as e:
            chroma_status = {'connected': False, 'error': str(e)}
        
        # Retrain status
        retrain_status = {'last_run': None, 'outcomes_available': 0, 'should_retrain': False}
        try:
            from self_learning.tracker import OutcomeTracker
            tracker = OutcomeTracker()
            summary = tracker.get_summary(days=30)
            retrain_status['outcomes_available'] = summary.get('total', 0)
            retrain_status['win_rate'] = summary.get('win_rate', 0)
            
            from self_learning.retrainer import ModelRetrainer
            retrainer = ModelRetrainer()
            retrain_status['should_retrain'] = retrainer.should_retrain(min_outcomes=10, accuracy_threshold=0.55)
        except Exception as e:
            retrain_status['error'] = str(e)
        
        return jsonify({
            'pipeline': orch.get_dashboard_data(),
            'mt5_cache': mt5_status,
            'chromadb': chroma_status,
            'retrain': retrain_status,
            'timestamp': datetime.now().isoformat(),
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting orchestrator status: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/backtest/results', methods=['GET'])
@limiter.limit("60 per minute")
def get_backtest_results():
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
            'silver': 'silver_backtest.json',
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
@limiter.limit("6 per hour")
def run_backtest():
    """Run backtest with specified parameters."""
    try:
        params = request.json
        start_date = params.get('start_date')
        end_date = params.get('end_date')
        asset = params.get('asset', 'gold').lower()
        
        if asset not in ['gold', 'silver']:
            return jsonify({'error': 'Invalid asset. Must be "gold" or "silver"'}), 400
        
        logger.info(f"Running {asset} backtest from {start_date} to {end_date}")
        
        result, status_code = backtest_manager.run(start_date, end_date, asset=asset)
        return jsonify(result), status_code
    
    except Exception as e:
        logger.error(f"Error starting backtest: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/backtest/status', methods=['GET'])
def get_backtest_status():
    """Get current backtest execution status and progress."""
    status = backtest_manager.get_status()
    return jsonify(status), 200


@app.route('/api/shap/feature-importance', methods=['GET'])
@token_required
@limiter.limit("60 per minute")  # FIXED: Add rate limiting
def get_shap_feature_importance(current_user_email):
        """Get SHAP feature importance data with real computation.
        
        Query params:
            asset: "gold" or "silver" (default: gold)
            recompute: "true" to force recomputation (default: false)
        """
        try:
            from api.app.shap_cache import shap_cache
            
            asset = request.args.get('asset', 'gold').lower()
            recompute = request.args.get('recompute', 'false').lower() == 'true'
            
            if not recompute:
                # Try to return cached data
                cached = shap_cache.get(asset)
                if cached.get('computed'):
                    logger.info(f"Returning cached SHAP data for {asset}")
                    return jsonify(cached)
            
            # Try to compute real SHAP values
            logger.info(f"Computing SHAP values for {asset}...")
            
            # Load model
            model, feature_names = model_manager.get_or_load_model(asset)
            if model is None:
                logger.warning(f"Model not available for {asset}")
                return jsonify(shap_cache.get(asset))
            
            # Load sample data for SHAP computation
            try:
                if asset == "gold":
                    df = load_gold_data(primary_tf="15m", session_filter=True)
                else:
                    df = load_silver_data(primary_tf="15m", session_filter=True)
                
                # Engineer features
                df = engineer_all_features(df, add_labels=False, asset=asset)
                
                # Drop target if present
                if 'target' in df.columns:
                    df = df.drop(columns=['target'])
                
                # Sample for SHAP (limit to 1000 for speed)
                if len(df) > 1000:
                    df_sample = df.sample(n=1000, random_state=42)
                else:
                    df_sample = df
                
                # Compute SHAP
                importance_dict = shap_cache.compute_shap_for_asset(asset, model, df_sample)
                
                logger.info(f"✅ SHAP computed for {asset}: {len(importance_dict.get('feature_importance', []))} features")
                return jsonify(importance_dict)
            
            except Exception as e:
                logger.error(f"Error computing SHAP: {e}")
                logger.warning(f"Falling back to cached/mock SHAP for {asset}")
                return jsonify(shap_cache.get(asset))
        
        except Exception as e:
            logger.error(f"Error in SHAP endpoint: {e}")
            return jsonify({'error': str(e)}), 500


@app.route('/api/shap/plot', methods=['GET'])
@token_required
def get_shap_plot(current_user_email):
    """Serve SHAP feature importance plot. Auto-generates on first request."""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        
        project_root = Path(__file__).parent.parent.parent
        plot_dir = project_root / 'reports' / 'shap_plots'
        plot_file = plot_dir / 'feature_importance.png'
        
        if not plot_file.exists():
            # Auto-generate from cached SHAP data
            asset = request.args.get('asset', 'gold')
            shap_data = shap_cache.get(asset)
            features = shap_data.get('feature_importance', [])
            
            if not features:
                return jsonify({'error': 'No SHAP data available'}), 404
            
            plot_dir.mkdir(parents=True, exist_ok=True)
            
            names = [f['feature'] for f in features[:15]][::-1]
            values = [f['importance'] for f in features[:15]][::-1]
            
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.barh(names, values, color='#10b981')
            ax.set_xlabel('Mean |SHAP Value|')
            ax.set_title(f'SHAP Feature Importance — {asset.upper()}')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            plt.tight_layout()
            plt.savefig(plot_file, dpi=150, bbox_inches='tight')
            plt.close(fig)
            logger.info(f"SHAP plot generated: {plot_file}")
        
        return send_file(plot_file, mimetype='image/png')
    
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
            model_path = MODELS_DIR / 'silver_enhanced_15m.pkl'
        
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

def start_prediction_updates():
    """Background thread to emit real-time prediction updates."""
    global thread_running
    thread_running = True
    
    logger.info("Starting real-time prediction updates thread")
    
    while thread_running:
        try:
            # Generate predictions for both assets
            for asset in ['gold', 'silver']:
                if not connected_clients:
                    continue
                    
                # Check if any clients are subscribed to this asset
                clients_subscribed = any(
                    client_data.get('subscriptions', {}).get('predictions', {}).get(asset, False)
                    for client_data in connected_clients.values()
                )
                
                if not clients_subscribed:
                    continue
                
                # Generate fresh predictions
                try:
                    prediction_data = generate_predictions_for_asset(asset)
                    if prediction_data and prediction_data['predictions']:
                        # Emit the latest prediction as a PredictionItem (not the wrapper)
                        latest = prediction_data['predictions'][-1]
                        socketio.emit('predictions', latest)
                        logger.debug(f"Emitted {asset} prediction to {len(connected_clients)} clients")
                except Exception as e:
                    logger.error(f"Error generating predictions for {asset}: {e}")
                    
        except Exception as e:
            logger.error(f"Error in prediction updates thread: {e}")
            
        # Wait 30 seconds before next update
        time.sleep(30)
    
    logger.info("Real-time prediction updates thread stopped")


def generate_predictions_for_asset(asset: str) -> Dict[str, Any]:
    """Generate predictions for a specific asset using cache-aware data loading."""
    try:
        cache_key = f"{asset}_predictions"
        df = prediction_cache.get(cache_key)

        if df is None:
            logger.info(f"Cache miss for {asset} — loading data and engineering features...")
            df = load_asset_data(asset=asset, primary_tf='15m', session_filter=True)
            if df is None or df.empty:
                logger.warning(f"No data loaded for asset {asset}")
                return None

            df = engineer_all_features(df, add_labels=False)
            if df is None or df.empty:
                logger.warning(f"Feature engineering returned no data for {asset}")
                return None

            prediction_cache.set(cache_key, df)
        else:
            logger.debug(f"Using cached data for {asset}")

        current_price = float(df.iloc[-1]['close']) if 'close' in df.columns else 2000.0

        model, feature_names = model_manager.get_or_load_model(asset)
        if model is None:
            logger.warning(f"No model available for asset {asset}")
            return None

        if feature_names:
            # Create DataFrame with exactly the features the model expects
            # Missing features are filled with 0, extra features are dropped
            X = pd.DataFrame(index=df.index)
            for feat in feature_names:
                if feat in df.columns:
                    X[feat] = df[feat]
                else:
                    X[feat] = 0.0  # Fill missing features with 0
            
            if X.empty:
                logger.warning(f"No matching features found for asset {asset}")
                return None
        else:
            X = df.select_dtypes(include=['float64', 'int64'])

        if X.empty:
            logger.warning(f"No valid feature columns for asset {asset}")
            return None

        predictions = model.predict(X)
        try:
            probabilities = model.predict_proba(X)[:, 1]
        except Exception:
            probabilities = [0.5] * len(predictions)

        last_n = 10
        start = max(0, len(predictions) - last_n)
        results = []
        for idx in range(start, len(predictions)):
            results.append({
                'timestamp': df.index[idx].isoformat() if hasattr(df.index[idx], 'isoformat') else str(df.index[idx]),
                'signal': int(predictions[idx]),
                'probability': float(probabilities[idx]),
                'price': float(df.iloc[idx]['close']) if 'close' in df.columns else current_price,
            })

        return {
            'predictions': results,
            'total_signals': int(sum(results_item['signal'] for results_item in results)),
            'current_price': current_price,
        }
    except Exception as e:
        logger.error(f"generate_predictions_for_asset({asset}) failed: {e}")
        import traceback
        traceback.print_exc()
        return None



@app.route('/api/backtest/export', methods=['GET'])
@limiter.limit("30 per minute")
def export_backtest():
    """Export backtest results as CSV or PDF.
    
    Query params:
        format: 'csv' or 'pdf' (default: csv)
        type: 'trades', 'summary', 'equity', or 'all' (default: all, CSV only)
    """
    try:
        from backtesting.export import BacktestExporter
        import io

        fmt = request.args.get('format', 'csv').lower()
        export_type = request.args.get('type', 'all').lower()

        results_path = Path(__file__).parent.parent.parent / 'reports' / 'backtest_results' / 'latest.json'
        if not results_path.exists():
            return jsonify({'error': 'No backtest results found. Run a backtest first.'}), 404

        with open(results_path, 'r') as f:
            data = json.load(f)

        exporter = BacktestExporter()

        if fmt == 'pdf':
            buf = io.BytesIO()
            success = exporter.export_pdf(data, buf)
            if not success:
                return jsonify({'error': 'PDF generation failed'}), 500
            buf.seek(0)
            return send_file(buf, mimetype='application/pdf',
                           as_attachment=True,
                           download_name='backtest_report.pdf')

        # CSV exports
        if export_type == 'all':
            buf = io.BytesIO()
            writer = io.TextIOWrapper(buf, encoding='utf-8')
            # Combine all into one CSV
            import pandas as pd
            summary_df = pd.DataFrame([data.get('summary', {})])
            equity_df = pd.DataFrame(data.get('equity_curve', []))
            trades_df = pd.DataFrame(data.get('trades', []))

            writer.write("# Summary\n")
            summary_df.to_csv(writer, index=False)
            writer.write("\n# Equity Curve\n")
            equity_df.to_csv(writer, index=False)
            writer.write("\n# Trades\n")
            trades_df.to_csv(writer, index=False)
            writer.flush()
            buf.seek(0)
            return send_file(buf, mimetype='text/csv',
                           as_attachment=True,
                           download_name='backtest_report.csv')

        # Individual CSV export
        buf = io.BytesIO()
        if export_type == 'trades':
            exporter.export_trades_csv(data, buf)
        elif export_type == 'summary':
            exporter.export_summary_csv(data, buf)
        elif export_type == 'equity':
            exporter.export_equity_csv(data, buf)
        else:
            return jsonify({'error': f'Unknown export type: {export_type}'}), 400

        buf.seek(0)
        return send_file(buf, mimetype='text/csv',
                       as_attachment=True,
                       download_name=f'backtest_{export_type}.csv')

    except Exception as e:
        logger.error(f"Error exporting backtest: {e}")
        return jsonify({'error': str(e)}), 500


# WebSocket event handlers for real-time features
@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    global prediction_thread, thread_running
    
    client_id = request.sid
    connected_clients[client_id] = {
        'connected_at': datetime.now(timezone.utc),
        'subscriptions': {}
    }
    
    logger.info(f'Client {client_id} connected. Total clients: {len(connected_clients)}')
    emit('connected', {'status': 'success'})
    
    # Start prediction thread if this is the first client
    if len(connected_clients) == 1 and (prediction_thread is None or not thread_running):
        prediction_thread = threading.Thread(target=start_prediction_updates, daemon=True)
        prediction_thread.start()
        logger.info("Started prediction updates thread")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    global thread_running
    
    client_id = request.sid
    if client_id in connected_clients:
        del connected_clients[client_id]
        logger.info(f'Client {client_id} disconnected. Total clients: {len(connected_clients)}')
    
    # Stop thread if no clients remain
    if len(connected_clients) == 0 and thread_running:
        thread_running = False
        logger.info("Stopped prediction updates thread")

@socketio.on('subscribe_predictions')
def handle_subscribe_predictions(data):
    """Subscribe to real-time prediction updates."""
    client_id = request.sid
    asset = data.get('asset', 'gold') if isinstance(data, dict) else 'gold'
    
    if client_id in connected_clients:
        if 'predictions' not in connected_clients[client_id]['subscriptions']:
            connected_clients[client_id]['subscriptions']['predictions'] = {}
        connected_clients[client_id]['subscriptions']['predictions'][asset] = True
        
        logger.info(f'Client {client_id} subscribed to {asset} predictions')
        emit('subscription_confirmed', {'type': 'predictions', 'asset': asset})
    else:
        logger.warning(f'Unknown client {client_id} tried to subscribe to predictions')

@socketio.on('subscribe_etl_status')
def handle_subscribe_etl_status(data):
    """Subscribe to ETL pipeline status updates."""
    logger.info(f'Client subscribed to ETL status: {data}')
    emit('subscription_confirmed', {'type': 'etl_status'})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
