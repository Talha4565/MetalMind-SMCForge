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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# WSGI middleware: handle CORS for ALL paths including /socket.io
ALLOWED_ORIGINS = {"http://localhost:3000", "http://127.0.0.1:3000", "http://192.168.1.102:3000"}

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
    cors_allowed_origins="*",
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
    allowed_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # CORS for API routes
    if request.path.startswith('/api') or request.path.startswith('/auth'):
        if origin in allowed_origins:
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
        connect_src = "connect-src 'self' https://yourdomain.com wss://yourdomain.com; "
    
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-eval' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://s.tradingview.com https://unpkg.com; "
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

from api.app.alert_routes import alert_bp
app.register_blueprint(alert_bp)


# FIXED: Encapsulate all global state in proper classes for thread safety and testability
MODELS_DIR = Path(__file__).parent.parent.parent / 'models'

class ModelManager:
    """Thread-safe model management with lazy loading."""
    
    def __init__(self):
        self._models = {}
        self._feature_names = {}
        self._v4_models = {}
        self._lock = threading.Lock()
        self.models_dir = MODELS_DIR
    
    def load_model(self, asset: str) -> tuple:
        """Load model for specific asset."""
        model_path = self.models_dir / f'{asset}_enhanced_15m.pkl'
        if not model_path.exists():
            if asset == "gold":
                model_path = self.models_dir / 'enhanced_15m.pkl'
            elif asset == "silver":
                model_path = self.models_dir / 'processed' / 'silver_model_enhanced.pkl'
            else:
                return None, None
        
        if not model_path.exists():
            logger.warning(f"Model file not found for {asset}: {model_path}")
            return None, None
        
        try:
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
                if isinstance(model_data, dict):
                    model = model_data['model']
                    feature_names = model_data.get('features', None)
                else:
                    model = model_data
                    try:
                        feature_names = list(model.feature_names_in_) if hasattr(model, 'feature_names_in_') else None
                    except (AttributeError, Exception):
                        feature_names = None
            
            if feature_names is not None:
                logger.info(f"{asset.upper()} model loaded: {len(feature_names)} features")
            else:
                logger.info(f"{asset.upper()} model loaded")
            
            return model, feature_names
        
        except Exception as e:
            logger.error(f"Failed to load {asset} model: {e}")
            return None, None
    
    def load_v4_model(self, asset: str) -> dict:
        """Load v4 regression model (direction + TP/SL)."""
        if asset in self._v4_models:
            return self._v4_models[asset]
        
        v4_path = self.models_dir / f'{asset}_regression_system.pkl'
        if not v4_path.exists():
            logger.warning(f"v4 model not found: {v4_path}")
            return None
        
        try:
            with open(v4_path, 'rb') as f:
                data = pickle.load(f)
            self._v4_models[asset] = data
            logger.info(f"v4 model loaded for {asset}: direction + TP/SL")
            return data
        except Exception as e:
            logger.error(f"Failed to load v4 model: {e}")
            return None
    
    def get_or_load_model(self, asset: str) -> tuple:
        """Get model, loading it lazily if needed. Thread-safe."""
        with self._lock:
            if asset not in self._models:
                logger.info(f"Lazy loading {asset} model...")
                self._models[asset], self._feature_names[asset] = self.load_model(asset)
                if self._models[asset] is None:
                    logger.warning(f"Model not found for {asset}. Train it first.")
            return self._models.get(asset), self._feature_names.get(asset)
    
    def is_loaded(self, asset: str) -> bool:
        with self._lock:
            return asset in self._models and self._models[asset] is not None
    
    def get_loaded_models(self) -> dict:
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
                import subprocess, sys
                project_root = Path(__file__).parent.parent.parent

                with self._lock:
                    self._status['progress'] = 10

                result = subprocess.run(
                    [sys.executable, 'run.py', '--mode', 'backtest', '--asset', asset],
                    capture_output=True, text=True, cwd=str(project_root), timeout=300
                )

                with self._lock:
                    self._status['progress'] = 80

                if result.returncode == 0:
                    results_dir = project_root / 'reports' / 'backtest_results'
                    latest_file = results_dir / 'latest.json'
                    backtest_result = None
                    if latest_file.exists():
                        with open(latest_file) as f:
                            backtest_result = json.load(f)

                    with self._lock:
                        self._status = {
                            'running': False, 'progress': 100, 'error': None,
                            'result': backtest_result
                        }
                else:
                    with self._lock:
                        self._status = {
                            'running': False, 'progress': 0,
                            'error': result.stderr or 'Unknown error', 'result': None
                        }
            except subprocess.TimeoutExpired:
                with self._lock:
                    self._status = {'running': False, 'progress': 0, 'error': 'Timeout', 'result': None}
            except Exception as e:
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

# NEW: Response cache for API endpoints (saves 500ms-2s per request)
class ResponseCache:
    """Simple in-memory cache for API responses with TTL."""
    
    def __init__(self):
        self._cache = {}
        self._lock = threading.Lock()
    
    def get(self, key: str):
        with self._lock:
            if key in self._cache:
                data, expiry = self._cache[key]
                if datetime.now(timezone.utc) < expiry:
                    return data
                del self._cache[key]
        return None
    
    def set(self, key: str, data, ttl_seconds: int = 30):
        with self._lock:
            expiry = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
            self._cache[key] = (data, expiry)
    
    def clear(self, key: str = None):
        with self._lock:
            if key:
                self._cache.pop(key, None)
            else:
                self._cache.clear()

response_cache = ResponseCache()

# Circuit breaker for external API calls (Yahoo Finance)
class CircuitBreaker:
    """Prevents cascading failures when external services are down."""
    
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self._failure_count = 0
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._last_failure_time = None
        self._state = 'closed'  # closed, open, half-open
        self._lock = threading.Lock()
    
    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        with self._lock:
            if self._state == 'open':
                if self._last_failure_time and \
                   (datetime.now(timezone.utc) - self._last_failure_time).total_seconds() > self._recovery_timeout:
                    self._state = 'half-open'
                    logger.info("Circuit breaker: half-open, trying request")
                else:
                    raise Exception("Circuit breaker OPEN - external service unavailable")
        
        try:
            result = func(*args, **kwargs)
            with self._lock:
                self._failure_count = 0
                self._state = 'closed'
            return result
        except Exception as e:
            with self._lock:
                self._failure_count += 1
                self._last_failure_time = datetime.now(timezone.utc)
                if self._failure_count >= self._failure_threshold:
                    self._state = 'open'
                    logger.warning(f"Circuit breaker OPEN after {self._failure_count} failures")
            raise
    
    def get_state(self):
        with self._lock:
            return {
                'state': self._state,
                'failure_count': self._failure_count,
                'last_failure': self._last_failure_time.isoformat() if self._last_failure_time else None
            }

MT5_SYMBOLS = {'gold': 'XAUUSD', 'silver': 'XAGUSD'}
MT5_CACHE_FILE = Path(__file__).parent.parent.parent / 'reports' / 'mt5_prices.json'

def fetch_mt5_price(asset: str) -> dict:
    """Fetch live spot price from MT5 price cache file."""
    try:
        if MT5_CACHE_FILE.exists():
            import json
            prices = json.loads(MT5_CACHE_FILE.read_text())
            data = prices.get(asset)
            if data:
                # Check if cache is fresh (less than 30 seconds old)
                cache_time = datetime.fromisoformat(data['timestamp'])
                age = (datetime.now(timezone.utc) - cache_time).total_seconds()
                if age < 30:
                    return data
                else:
                    logger.debug(f"MT5 cache stale ({age:.0f}s old)")
        return None
    except Exception as e:
        logger.error(f"MT5 cache read failed: {e}")
        return None


# Initialize prediction logger and email alerts
from etl.prediction_logger import PredictionLogger
from etl.alerts import EmailAlertService
from etl.guards.alert_risk_gate import AlertRiskGate
from etl.agents.llm_client import NemotronClient
from etl.agents.signal_reasoner import SignalReasoner

prediction_logger = PredictionLogger()
email_alerts = EmailAlertService(confidence_threshold=0.70)
# Deterministic gate — runs unconditionally on every candidate alert.
alert_risk_gate = AlertRiskGate()
# LLM agent — off by default (ML_AGENT_ENABLED). Fail-open. Backtest path never imports this.
signal_reasoner = SignalReasoner(client=NemotronClient(), pred_logger=prediction_logger)

logger.info("✅ Server ready - models will be loaded on first request (lazy loading)")
logger.info("✅ ModelManager, PredictionCache, BacktestManager, PredictionLogger initialized")


@app.route('/api/health', methods=['GET'])
@limiter.limit("10 per minute")
def health_check():
    """Health check with long-polling support.

    Send If-None-Match header with previous ETag to hold connection
    until status changes (up to 30s).
    """
    from api.app.long_poll import long_poll, make_etag

    def _check():
        try:
            from api.app.database import db, get_pool_stats
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            db_healthy = True
        except Exception:
            db_healthy = False

        models_status = model_manager.get_loaded_models()
        pool_stats = get_pool_stats()

        project_root = Path(__file__).parent.parent.parent
        fs_healthy = (project_root / 'reports').exists() and (project_root / 'models').exists()

        overall_healthy = db_healthy

        data = {
            'status': 'healthy' if overall_healthy else 'degraded',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'checks': {
                'database': 'ok' if db_healthy else 'error',
                'filesystem': 'ok' if fs_healthy else 'error',
                'models': models_status,
                'connection_pool': pool_stats,
            },
            'version': '1.0.0',
        }
        return make_etag(data), data

    return long_poll(etag_key='health', check_fn=_check, timeout=30)


@app.route('/api/market/price', methods=['GET'])
@limiter.limit("30 per minute")
def get_live_price():
    """Fetch real-time spot price from MT5 (cached for 10s).
    
    Query params:
        asset: gold or silver (default: gold)
    """
    try:
        asset = request.args.get('asset', 'gold').lower()
        
        if asset not in MT5_SYMBOLS:
            return jsonify({'error': 'Invalid asset. Must be "gold" or "silver"'}), 400
        
        # Check cache first (10s TTL for live prices)
        cache_key = f"price_{asset}"
        cached = response_cache.get(cache_key)
        if cached:
            return jsonify(cached)
        
        # Fetch from MT5
        mt5_data = fetch_mt5_price(asset)
        
        if mt5_data:
            result = {
                'asset': asset,
                'price': mt5_data['ask'],
                'bid': mt5_data['bid'],
                'ask': mt5_data['ask'],
                'spread': mt5_data['spread'],
                'source': 'MT5',
                'timestamp': datetime.now(timezone.utc).isoformat(),
            }
        else:
            return jsonify({'error': 'MT5 price cache unavailable. Ensure MT5 is running.', 'asset': asset}), 503
        
        # Cache for 10 seconds
        response_cache.set(cache_key, result, ttl_seconds=10)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error fetching live price: {e}")
        # Return cached data if available, even if expired
        stale = response_cache.get(cache_key)
        if stale:
            stale['stale'] = True
            return jsonify(stale)
        return jsonify({'error': 'Price data temporarily unavailable', 'asset': asset}), 503


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
        
        # Check response cache first (30s TTL)
        resp_cache_key = f"predictions_{asset}_{limit}"
        cached_response = response_cache.get(resp_cache_key)
        if cached_response:
            return jsonify(cached_response)
        
        # FIXED: Use ModelManager for lazy loading
        model, feature_names = model_manager.get_or_load_model(asset)
        if model is None:
            return jsonify({'error': f'Model not found for {asset}. Train it first.'}), 404
        
        # Load v4 model (direction + TP/SL)
        v4_data = model_manager.load_v4_model(asset)
        
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
        
        # Work on a COPY to avoid corrupting the cached dataframe
        df = df.copy()
        
        # Inject current live spot price from MT5
        try:
            mt5_data = fetch_mt5_price(asset)
            if mt5_data:
                live_price = mt5_data['ask']
            else:
                logger.warning(f"MT5 price cache unavailable for {asset}, using last known price")
                live_price = None
            
            if live_price:
                latest_idx = df.index[-1]
                df.loc[latest_idx, 'close'] = live_price
                df.loc[latest_idx, 'open'] = live_price
                df.loc[latest_idx, 'high'] = live_price
                df.loc[latest_idx, 'low'] = live_price
                df.loc[latest_idx, 'price'] = live_price
                logger.info(f"Injected live spot price ${live_price:.2f} into latest {asset} bar")
        except Exception as e:
            logger.warning(f"Could not fetch live price for prediction: {e}")
        
        # Get most recent N bars
        recent_data = df.iloc[-limit:].copy()
        
        # FIXED: Robustly align column names with model expectations
        X_input = recent_data.copy()
        
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
            except KeyError as e:
                logger.error(f"Final alignment failed. Missing: {e}")
                available_features = [f for f in feature_names if f in X_input.columns]
                X = X_input[available_features]
        else:
            X = X_input.select_dtypes(include=['float64', 'int64'])

        # === V4 MODEL: Direction + TP/SL with trend filter ===
        if v4_data is not None:
            dir_model = v4_data['direction_model']
            tp_model = v4_data['tp_model']
            sl_model = v4_data['sl_model']
            v4_features = v4_data['features']
            
            # Add v4-specific features that aren't in standard pipeline
            def compute_adx_local(df, period=14):
                h, l, c = df["high"], df["low"], df["close"]
                pdm = h.diff()
                mdm = -l.diff()
                pdm = pdm.where((pdm > mdm) & (pdm > 0), 0.0)
                mdm = mdm.where((mdm > pdm) & (mdm > 0), 0.0)
                tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
                atr = tr.rolling(period).mean()
                pdi = 100 * pdm.rolling(period).mean() / atr
                mdi = 100 * mdm.rolling(period).mean() / atr
                dx = 100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan)
                return dx.rolling(period).mean()
            
            def compute_cvd_local(df):
                delta = df["close"] - df["open"]
                return (np.sign(delta) * df["volume"]).cumsum()
            
            # Add features to X_input
            if 'cvd_15m' not in X_input.columns:
                X_input['cvd_15m'] = compute_cvd_local(X_input)
                X_input['cvd_15m_slope'] = X_input['cvd_15m'].diff(5)
            
            if 'cvd_30m' not in X_input.columns:
                # Approximate 30m CVD using rolling sum
                X_input['cvd_30m'] = X_input['cvd_15m'].rolling(2).sum()
                X_input['cvd_30m_slope'] = X_input['cvd_30m'].diff(5)
            
            if 'adx_14' not in X_input.columns:
                X_input['adx_14'] = compute_adx_local(X_input, 14)
                X_input['adx_trending'] = (X_input['adx_14'] > 25).astype(int)
            
            # ATR
            if 'atr_14' not in X_input.columns:
                tr = pd.concat([
                    X_input["high"] - X_input["low"],
                    (X_input["high"] - X_input["close"].shift()).abs(),
                    (X_input["low"] - X_input["close"].shift()).abs(),
                ], axis=1).max(axis=1)
                X_input['atr_14'] = tr.rolling(14).mean()
            
            # 1h trend features (use 1h data if available)
            if 'trend_ema_cross' not in X_input.columns:
                # Simple trend proxy using 15m data
                ema50 = X_input['close'].ewm(span=50, adjust=False).mean()
                ema200 = X_input['close'].ewm(span=200, adjust=False).mean()
                X_input['trend_ema_cross'] = (ema50 > ema200).astype(int)
                X_input['trend_price_vs_ema'] = ((X_input['close'] - ema50) / ema50).clip(-0.05, 0.05)
                X_input['trend_adx'] = compute_adx_local(X_input, 14)
                X_input['trend_strength'] = X_input['trend_adx'].clip(0, 50) / 50
            
            # Ensure all v4 features exist
            for feat in v4_features:
                if feat not in X_input.columns:
                    X_input[feat] = 0.0
            
            # Direction predictions
            proba = dir_model.predict_proba(X_input[v4_features])[:, 1]
            confident = np.abs(proba - 0.5) >= 0.15
            preds_raw = (proba >= 0.5).astype(int)
            
            # Trend filter
            if 'trend_ema_cross' in X_input.columns:
                trend = X_input['trend_ema_cross'].values
                aligned = np.where(
                    (preds_raw == 1) & (trend == 1), 1,
                    np.where((preds_raw == 0) & (trend == 0), 0, -1)
                )
            else:
                aligned = preds_raw
            predictions = np.where(confident, aligned, -1)
            probabilities = np.where(proba >= 0.5, proba, 1 - proba)
            
            # TP/SL predictions
            tp_pred = np.clip(tp_model.predict(X_input[v4_features]), 0.003, 0.02)
            sl_pred = np.clip(sl_model.predict(X_input[v4_features]), 0.00375, 0.0075)
            
            logger.info(f"v4 predictions: {(predictions==1).sum()} BUY, {(predictions==0).sum()} SELL, {(predictions==-1).sum()} HOLD")
        else:
            # Fallback to old model
            raw_predictions = model.predict(X)
            predictions = np.where(raw_predictions == 0, -1, np.where(raw_predictions == 1, 0, 1))
            try:
                proba = model.predict_proba(X)
                probabilities = proba.max(axis=1)
            except (AttributeError, IndexError):
                probabilities = [0.5] * len(predictions)
            tp_pred = [0.003] * len(predictions)
            sl_pred = [0.003] * len(predictions)
        
        # Compute real SHAP values for the latest bar
        shap_values_for_response = [{'feature': 'N/A', 'contribution': 0.0}] * len(predictions)
        try:
            if SHAP_AVAILABLE and len(X) > 0:
                explainer = shap.TreeExplainer(model)
                latest_bar = X.iloc[[-1]]
                shap_vals = explainer.shap_values(latest_bar)
                if isinstance(shap_vals, list):
                    shap_vals = shap_vals[1]
                shap_vals = shap_vals[0]
                top_idx = np.argsort(np.abs(shap_vals))[::-1][:5]
                top_shap = [
                    {'feature': X.columns[j], 'contribution': float(shap_vals[j])}
                    for j in top_idx
                ]
                shap_values_for_response[-1] = top_shap
        except Exception as e:
            logger.warning(f"SHAP computation failed for prediction: {e}")
        
        # Prepare response
        results = []
        for i, (idx, row) in enumerate(recent_data.iterrows()):
            bar_shap = shap_values_for_response[-1] if i == len(recent_data) - 1 else shap_values_for_response[0]
            if isinstance(bar_shap, dict):
                bar_shap = [bar_shap]
            
            price = float(row['close'])
            signal = int(predictions[i])
            
            # Calculate TP/SL levels
            if signal == 1:  # BUY
                tp_level = price * (1 + tp_pred[i])
                sl_level = price * (1 - sl_pred[i])
            elif signal == 0:  # SELL
                tp_level = price * (1 - tp_pred[i])
                sl_level = price * (1 + sl_pred[i])
            else:  # HOLD
                tp_level = None
                sl_level = None
            
            results.append({
                'timestamp': idx.isoformat(),
                'asset': asset.upper(),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': price,
                'price': price,
                'signal': signal,
                'probability': float(probabilities[i]),
                'confidence': float(probabilities[i]),
                'tp_distance': round(float(tp_pred[i]) * 100, 3) if signal != -1 else None,
                'sl_distance': round(float(sl_pred[i]) * 100, 3) if signal != -1 else None,
                'tp_level': round(tp_level, 2) if tp_level else None,
                'sl_level': round(sl_level, 2) if sl_level else None,
                'shap_values': bar_shap
            })
        
        # Log the latest prediction and check for alerts
        if results:
            latest = results[-1]
            prediction_logger.log_prediction(
                asset=asset,
                signal=latest['signal'],
                confidence=latest['confidence'],
                price=latest['price'],
                shap_values=latest.get('shap_values', []),
                tp_distance=latest.get('tp_distance'),
                sl_distance=latest.get('sl_distance'),
            )
            
            # Create price alert if BUY/SELL with TP/SL
            if latest['signal'] in (1, 0) and latest.get('tp_level') and latest.get('sl_level'):
                from api.app.price_alerts import add_alert
                add_alert(
                    asset=asset,
                    signal=latest['signal'],
                    entry_price=latest['price'],
                    tp_level=latest['tp_level'],
                    sl_level=latest['sl_level'],
                    confidence=latest['confidence'],
                )
            
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
        
        response_data = {
            'asset': asset,
            'predictions': results,
            'total_signals': int(predictions.sum()),
            'data_range': {
                'start': recent_data.index.min().isoformat(),
                'end': recent_data.index.max().isoformat()
            }
        }
        
        # Cache response for 30 seconds
        response_cache.set(resp_cache_key, response_data, ttl_seconds=30)
        
        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Error getting predictions: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/backtest/results', methods=['GET'])
@token_required
@limiter.limit("60 per minute")  # FIXED: Add rate limiting
def get_backtest_results(current_user_email):
    """Get backtest results (cached for 60s).
    
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
        
        # Check cache first
        cache_key = f"backtest_{asset}"
        cached = response_cache.get(cache_key)
        if cached:
            return jsonify(cached)
        
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
            return jsonify([]), 200
        
        with open(results_file, 'r') as f:
            data = json.load(f)
        
        # Add asset identifier to response
        data['asset'] = asset if asset in ['gold', 'silver'] else 'latest'
        
        # Frontend expects an array of results
        result_list = [data]
        
        # Cache for 60 seconds
        response_cache.set(cache_key, result_list, ttl_seconds=60)
        
        return jsonify(result_list)
    
    except Exception as e:
        logger.error(f"Error loading backtest results: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/backtest/run', methods=['POST'])
@token_required
@limiter.limit("1 per hour")
def run_backtest(current_user_email):
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
@token_required
def get_backtest_status(current_user_email):
    """Backtest status with long-polling support.

    Holds connection until progress changes or backtest completes.
    """
    from api.app.long_poll import long_poll, make_etag

    def _check():
        status = backtest_manager.get_status()
        return make_etag(status), status

    return long_poll(etag_key='backtest_status', check_fn=_check, timeout=30)


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


@app.route('/api/cache/stats', methods=['GET'])
@limiter.limit("10 per minute")
def get_cache_stats():
    """Get cache statistics for monitoring."""
    with response_cache._lock:
        cache_entries = len(response_cache._cache)
        valid_entries = sum(
            1 for _, (_, expiry) in response_cache._cache.items()
            if datetime.now(timezone.utc) < expiry
        )
    
    return jsonify({
        'total_entries': cache_entries,
        'valid_entries': valid_entries,
        'expired_entries': cache_entries - valid_entries,
        'timestamp': datetime.now(timezone.utc).isoformat()
    })


@app.route('/api/cache/clear', methods=['POST'])
@limiter.limit("5 per minute")
def clear_cache():
    """Clear all cached responses."""
    response_cache.clear()
    prediction_cache.clear()
    file_cache.clear()
    return jsonify({'message': 'All caches cleared', 'timestamp': datetime.now(timezone.utc).isoformat()})


@app.route('/api/circuit/status', methods=['GET'])
@limiter.limit("10 per minute")
def get_circuit_status():
    """Get circuit breaker status for external services."""
    return jsonify({
        'mt5_price_cache': 'active' if MT5_CACHE_FILE.exists() else 'inactive',
        'timestamp': datetime.now(timezone.utc).isoformat()
    })


@app.route('/api/risk/status', methods=['GET'])
@limiter.limit("30 per minute")
def get_risk_status():
    """Risk status with long-polling support."""
    from api.app.long_poll import long_poll, make_etag
    from api.app.risk_manager import risk_manager

    def _check():
        data = risk_manager.get_status()
        return make_etag(data), data

    return long_poll(etag_key='risk_status', check_fn=_check, timeout=30)


@app.route('/api/risk/can-trade', methods=['GET'])
@limiter.limit("30 per minute")
def check_can_trade():
    """Can-trade check with long-polling support."""
    from api.app.long_poll import long_poll, make_etag
    from api.app.risk_manager import risk_manager

    def _check():
        data = risk_manager.can_trade()
        return make_etag(data), data

    return long_poll(etag_key='risk_can_trade', check_fn=_check, timeout=30)


@app.route('/api/risk/lot-size', methods=['GET'])
@limiter.limit("30 per minute")
def get_lot_size():
    """Calculate lot size for a given ATR and symbol.
    Query params: atr (required), symbol (default: XAGUSD)
    """
    from api.app.risk_manager import risk_manager
    try:
        atr = float(request.args.get('atr', 0))
        symbol = request.args.get('symbol', 'XAGUSD')
        if atr <= 0:
            return jsonify({'error': 'ATR must be > 0'}), 400
        return jsonify(risk_manager.calculate_lot_size(atr, symbol))
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid ATR value'}), 400


@app.route('/api/risk/weekly', methods=['GET'])
@limiter.limit("10 per minute")
def get_weekly_stats():
    """Get weekly performance stats."""
    from api.app.risk_manager import risk_manager
    return jsonify(risk_manager.get_weekly_stats())


@app.route('/api/risk/log', methods=['POST'])
@limiter.limit("60 per minute")
def log_trade():
    """Log a completed trade. Body: {signal, prob, entry, atr, pnl, sl_hit, tp_hit}"""
    from api.app.risk_manager import risk_manager
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    required = ['signal', 'prob', 'entry', 'atr', 'pnl']
    for field in required:
        if field not in data:
            return jsonify({'error': f'Missing field: {field}'}), 400

    risk_manager.log_trade(
        signal=data['signal'],
        prob=float(data['prob']),
        entry=float(data['entry']),
        atr=float(data['atr']),
        pnl=float(data['pnl']),
        sl_hit=data.get('sl_hit', False),
        tp_hit=data.get('tp_hit', False),
    )
    return jsonify({'message': 'Trade logged', 'status': risk_manager.get_status()})


@app.before_request
def handle_request_timeout():
    """Track request start time for timeout detection."""
    request._start_time = time.time()


@app.after_request
def handle_request_completion(response):
    """Log slow requests and add timing header."""
    if hasattr(request, '_start_time'):
        duration = time.time() - request._start_time
        response.headers['X-Response-Time'] = f"{duration:.3f}s"
        if duration > 5.0:
            logger.warning(f"Slow request: {request.path} took {duration:.2f}s")
    return response


@app.errorhandler(500)
def handle_500(error):
    """Handle internal server errors gracefully."""
    logger.error(f"Internal server error: {str(error)}", exc_info=True)
    return jsonify({
        'error': 'Internal server error',
        'message': 'The server encountered an unexpected condition',
        'status_code': 500
    }), 500


@app.errorhandler(502)
def handle_502(error):
    """Handle bad gateway errors."""
    logger.error(f"Bad gateway error: {str(error)}")
    return jsonify({
        'error': 'Bad gateway',
        'message': 'The server received an invalid response from upstream',
        'status_code': 502
    }), 502


@app.errorhandler(503)
def handle_503(error):
    """Handle service unavailable errors."""
    logger.error(f"Service unavailable: {str(error)}")
    return jsonify({
        'error': 'Service unavailable',
        'message': 'The server is temporarily unable to handle the request',
        'status_code': 503
    }), 503


@app.route('/api/models/info', methods=['GET'])
@token_required
@limiter.limit("60 per minute")  # FIXED: Add rate limiting
def get_model_info(current_user_email):
    """Get model metadata and information (cached for 5 min).
    
    Query params:
        asset: Asset to get model info for (gold or silver, default: gold)
    """
    try:
        asset = request.args.get('asset', 'gold').lower()
        
        # Validate asset
        if asset not in ['gold', 'silver']:
            return jsonify({'error': 'Invalid asset. Must be "gold" or "silver"'}), 400
        
        # Check cache first
        cache_key = f"model_info_{asset}"
        cached = response_cache.get(cache_key)
        if cached:
            return jsonify(cached)
        
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
        
        # Cache for 5 minutes
        response_cache.set(cache_key, info, ttl_seconds=300)
        
        return jsonify(info)
    
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/predictions/history', methods=['GET'])
@limiter.limit("60 per minute")
def get_prediction_history():
    """Get historical signal predictions with outcomes.

    Query params:
        asset: gold | silver | all (default: all)
        signal: buy | sell | hold | all (default: all)
        days: number of days to look back (default: 7, max: 30)
        page: page number (default: 1)
        per_page: results per page (default: 50, max: 200)
    """
    try:
        asset_filter = request.args.get('asset', 'all').lower()
        signal_filter = request.args.get('signal', 'all').lower()
        days = min(int(request.args.get('days', 7)), 30)
        page = max(int(request.args.get('page', 1)), 1)
        per_page = min(int(request.args.get('per_page', 50)), 200)

        if asset_filter not in ('gold', 'silver', 'all'):
            return jsonify({'error': 'Invalid asset filter'}), 400
        if signal_filter not in ('buy', 'sell', 'all'):
            return jsonify({'error': 'Invalid signal filter'}), 400

        # Check outcomes for today's predictions before serving
        try:
            current_prices = {}
            for a in ('gold', 'silver'):
                mt5_data = fetch_mt5_price(a)
                if mt5_data:
                    current_prices[a] = mt5_data['ask']
            if current_prices:
                prediction_logger.check_outcomes(current_prices)
        except Exception as e:
            logger.warning(f"Outcome check failed: {e}")

        predictions_dir = Path(__file__).parent.parent.parent / 'reports' / 'predictions'
        if not predictions_dir.exists():
            return jsonify({'predictions': [], 'summary': _empty_summary(), 'total': 0, 'page': page, 'per_page': per_page})

        all_records = []
        for i in range(days):
            date_str = (datetime.now(timezone.utc) - timedelta(days=i)).strftime('%Y%m%d')
            log_file = predictions_dir / f'predictions_{date_str}.jsonl'
            if not log_file.exists():
                continue
            with open(log_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        all_records.append(record)
                    except json.JSONDecodeError:
                        continue

        # Apply filters
        if asset_filter != 'all':
            all_records = [r for r in all_records if r.get('asset') == asset_filter]
        # Always exclude HOLD — only show actionable BUY/SELL signals
        all_records = [r for r in all_records if r.get('signal') != 0]
        if signal_filter != 'all':
            signal_map = {'buy': 1, 'sell': -1}
            target_signal = signal_map.get(signal_filter)
            if target_signal is not None:
                all_records = [r for r in all_records if r.get('signal') == target_signal]

        # Sort newest first
        all_records.sort(key=lambda r: r.get('timestamp', ''), reverse=True)

        # Compute summary
        summary = _compute_signal_summary(all_records)

        # Paginate
        total = len(all_records)
        start = (page - 1) * per_page
        end = start + per_page
        page_records = all_records[start:end]

        return jsonify({
            'predictions': page_records,
            'summary': summary,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page,
        })

    except Exception as e:
        logger.error(f"Error getting prediction history: {e}")
        return jsonify({'error': str(e)}), 500


def _empty_summary():
    return {
        'total': 0, 'buys': 0, 'sells': 0, 'holds': 0,
        'wins': 0, 'losses': 0, 'win_rate': 0, 'avg_confidence': 0,
        'avg_pnl': 0,
    }


def _compute_signal_summary(records):
    total = len(records)
    buys = sum(1 for r in records if r.get('signal') == 1)
    sells = sum(1 for r in records if r.get('signal') == -1)
    holds = total - buys - sells
    wins = sum(1 for r in records if r.get('actual_outcome') and 'WIN' in r['actual_outcome'])
    losses = sum(1 for r in records if r.get('actual_outcome') and 'LOSS' in r['actual_outcome'])
    evaluated = wins + losses
    win_rate = round(wins / evaluated * 100, 1) if evaluated > 0 else 0
    avg_confidence = round(sum(r.get('confidence', 0) for r in records) / total, 4) if total > 0 else 0
    pnls = [r['actual_pnl'] for r in records if r.get('actual_pnl') is not None]
    avg_pnl = round(sum(pnls) / len(pnls), 2) if pnls else 0

    return {
        'total': total, 'buys': buys, 'sells': sells, 'holds': holds,
        'wins': wins, 'losses': losses, 'win_rate': win_rate,
        'avg_confidence': avg_confidence, 'avg_pnl': avg_pnl,
    }


# REMOVED: Flask UI serving routes - now using Next.js frontend
# All UI routes removed to make Flask API-only

def start_prediction_updates():
    """Background thread to emit real-time prediction + pipeline + price updates."""
    global thread_running
    thread_running = True

    logger.info("Starting real-time updates thread")

    while thread_running:
        try:
            if not connected_clients:
                time.sleep(5)
                continue

            # --- Pipeline status (every 60s) ---
            pipeline_subscribed = any(
                c.get('subscriptions', {}).get('pipeline')
                for c in connected_clients.values()
            )
            if pipeline_subscribed:
                try:
                    from api.app.pipeline_routes import _get_data_freshness_cached, _get_model_info_cached
                    gold_f = _get_data_freshness_cached('gold')
                    silver_f = _get_data_freshness_cached('silver')
                    gold_m = _get_model_info_cached('gold')
                    silver_m = _get_model_info_cached('silver')
                    all_fresh = gold_f['is_fresh'] and silver_f['is_fresh']
                    any_model = gold_m['exists'] or silver_m['exists']
                    socketio.emit('pipeline_update', {
                        'status': 'active' if all_fresh and any_model else 'degraded',
                        'data_freshness': {'gold': gold_f, 'silver': silver_f},
                        'models': {'gold': gold_m, 'silver': silver_m},
                        'last_update': gold_f['last_date'] or silver_f['last_date'],
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                    })
                except Exception as e:
                    logger.error(f"Pipeline emit error: {e}")

            # --- Live prices (every 15s) ---
            for asset in ['gold', 'silver']:
                price_subscribed = any(
                    c.get('subscriptions', {}).get('price', {}).get(asset)
                    for c in connected_clients.values()
                )
                if not price_subscribed:
                    continue
                try:
                    mt5_data = fetch_mt5_price(asset)
                    if mt5_data:
                        socketio.emit('price_update', {
                            'asset': asset,
                            'price': mt5_data['ask'],
                            'timestamp': datetime.now(timezone.utc).isoformat(),
                        })
                except Exception as e:
                    logger.error(f"Price emit error for {asset}: {e}")

            # Check price alerts every cycle
            try:
                prices = {}
                for asset in ['gold', 'silver']:
                    mt5_data = fetch_mt5_price(asset)
                    if mt5_data:
                        prices[asset] = mt5_data['ask']
                if prices:
                    from api.app.price_alerts import check_alerts
                    triggered = check_alerts(prices)
                    for alert in triggered:
                        socketio.emit('alert_triggered', {
                            'id': alert['id'],
                            'asset': alert['asset'],
                            'signal': alert['signal'],
                            'result': alert['result'],
                            'entry': alert['entry'],
                            'exit_price': alert.get('exit_price'),
                            'pnl_pct': alert.get('pnl_pct'),
                            'timestamp': datetime.now(timezone.utc).isoformat(),
                        })
            except Exception as e:
                logger.error(f"Alert check error: {e}")

            # --- Predictions (every 30s, existing logic) ---
            for asset in ['gold', 'silver']:
                clients_subscribed = any(
                    c.get('subscriptions', {}).get('predictions', {}).get(asset, False)
                    for c in connected_clients.values()
                )
                if not clients_subscribed:
                    continue
                try:
                    prediction_data = generate_predictions_for_asset(asset)
                    if prediction_data:
                        socketio.emit('predictions', {
                            'asset': asset,
                            'predictions': prediction_data['predictions'],
                            'total_signals': prediction_data['total_signals'],
                            'timestamp': datetime.now(timezone.utc).isoformat(),
                            'price': prediction_data['current_price']
                        })
                except Exception as e:
                    logger.error(f"Prediction emit error for {asset}: {e}")

        except Exception as e:
            logger.error(f"Error in updates thread: {e}")

        time.sleep(15)

    logger.info("Real-time updates thread stopped")


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
            available_features = [f for f in feature_names if f in df.columns]
            if not available_features:
                logger.warning(f"No matching features found for asset {asset}")
                return None
            X = df[available_features]
        else:
            X = df.select_dtypes(include=['float64', 'int64'])

        if X.empty:
            logger.warning(f"No valid feature columns for asset {asset}")
            return None

        raw_predictions = model.predict(X)
        # Remap from {0,1,2} -> {-1,0,1} (SELL,HOLD,BUY)
        predictions = np.where(raw_predictions == 0, -1, np.where(raw_predictions == 1, 0, 1))
        try:
            proba = model.predict_proba(X)
            probabilities = proba.max(axis=1)
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

        results_path = REPORTS_DIR / 'backtest_results' / 'latest.json'
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

@socketio.on('subscribe_pipeline')
def handle_subscribe_pipeline():
    """Subscribe to pipeline status updates."""
    client_id = request.sid
    if client_id in connected_clients:
        connected_clients[client_id]['subscriptions']['pipeline'] = True
        emit('subscription_confirmed', {'type': 'pipeline'})

@socketio.on('subscribe_price')
def handle_subscribe_price(data):
    """Subscribe to live price updates."""
    client_id = request.sid
    asset = data.get('asset', 'gold') if isinstance(data, dict) else 'gold'
    if client_id in connected_clients:
        if 'price' not in connected_clients[client_id]['subscriptions']:
            connected_clients[client_id]['subscriptions']['price'] = {}
        connected_clients[client_id]['subscriptions']['price'][asset] = True
        emit('subscription_confirmed', {'type': 'price', 'asset': asset})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
