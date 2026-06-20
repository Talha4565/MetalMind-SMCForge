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
from api.app.extensions import limiter, bcrypt, migrate
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
ALLOWED_ORIGINS = {"http://localhost:3000", "http://127.0.0.1:3000"}

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
    """Fetch real-time price from Yahoo Finance.
    
    Query params:
        asset: gold or silver (default: gold)
    """
    try:
        asset = request.args.get('asset', 'gold').lower()
        
        ticker_map = {
            'gold': 'GC=F',
            'silver': 'SI=F',
        }
        
        if asset not in ticker_map:
            return jsonify({'error': 'Invalid asset. Must be "gold" or "silver"'}), 400
        
        import requests as req
        ticker = ticker_map[asset]
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1m&range=1d"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = req.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        chart = resp.json()["chart"]["result"][0]
        meta = chart["meta"]
        
        return jsonify({
            'asset': asset,
            'price': float(meta["regularMarketPrice"]),
            'open': float(meta.get("chartPreviousClose", meta["regularMarketPrice"])),
            'high': float(meta.get("regularMarketPrice", 0)),
            'low': float(meta.get("regularMarketPrice", 0)),
            'volume': int(meta.get("regularMarketVolume", 0)),
            'timestamp': datetime.now(timezone.utc).isoformat(),
        })
    
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
            df = load_asset_data(asset=asset, primary_tf='15m', session_filter=True)
            
            # Apply feature engineering
            df = engineer_all_features(df, add_labels=False)
            
            # Cache the engineered data
            prediction_cache.set(cache_key, df)
        else:
            logger.info(f"Using cached data for {asset}")
        
        # Work on a COPY to avoid corrupting the cached dataframe
        df = df.copy()
        
        # Inject current live price into the latest bar
        try:
            import requests as req
            ticker_map = {'gold': 'XAUUSD=X', 'silver': 'XAGUSD=X'}
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker_map[asset]}?interval=1m&range=1d"
            resp = req.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            resp.raise_for_status()
            meta = resp.json()["chart"]["result"][0]["meta"]
            live_price = float(meta["regularMarketPrice"])
            
            # Update the latest bar with current price
            latest_idx = df.index[-1]
            df.loc[latest_idx, 'close'] = live_price
            df.loc[latest_idx, 'open'] = live_price
            df.loc[latest_idx, 'high'] = live_price
            df.loc[latest_idx, 'low'] = live_price
            df.loc[latest_idx, 'price'] = live_price
            logger.info(f"Injected live price ${live_price:.2f} into latest {asset} bar")
        except Exception as e:
            logger.warning(f"Could not fetch live price for prediction: {e}")
        
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
            probabilities = model.predict_proba(X)[:, 1]  # Probability of signal
        except (AttributeError, IndexError):
            # Fallback for models without predict_proba
            probabilities = [0.5] * len(predictions)
        
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
            # Use real SHAP for latest bar, placeholder for others
            bar_shap = shap_values_for_response[-1] if i == len(recent_data) - 1 else shap_values_for_response[0]
            
            results.append({
                'timestamp': idx.isoformat(),
                'asset': asset.upper(),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'price': float(row['close']), # FIXED: Expected by frontend (prediction.price)
                'signal': int(predictions[i]),
                'probability': float(probabilities[i]),
                'confidence': float(probabilities[i]), # FIXED: Expected by frontend (prediction.confidence)
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
                shap_values=latest.get('shap_values', [])
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
                    if prediction_data:
                        # Emit to all connected clients subscribed to this asset
                        socketio.emit('predictions', {
                            'asset': asset,
                            'predictions': prediction_data['predictions'],
                            'total_signals': prediction_data['total_signals'],
                            'timestamp': datetime.now(timezone.utc).isoformat(),
                            'price': prediction_data['current_price']
                        })
                        logger.debug(f"Emitted {asset} predictions to {len(connected_clients)} clients")
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


@app.route('/api/pipeline/status', methods=['GET'])
@limiter.limit("30 per minute")
def get_pipeline_status():
    """Get pipeline health, status, data freshness, and model backups."""
    try:
        from etl.orchestrator import PipelineOrchestrator
        orch = PipelineOrchestrator()
        return jsonify(orch.get_dashboard_data())
    except Exception as e:
        logger.error(f"Error getting pipeline status: {e}")
        return jsonify({'error': str(e)}), 500


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

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
