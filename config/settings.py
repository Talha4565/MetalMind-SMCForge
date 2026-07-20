"""
Configuration settings for ML-Signals trading system.
Maintains baseline parameters for reproducibility.
"""

import os
from pathlib import Path

# ============================================================================
# PROJECT PATHS
# ============================================================================
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"
GOLD_DATASET_DIR = PROJECT_ROOT / "Gold Dataset"
SILVER_DATASET_DIR = PROJECT_ROOT / "Silver Dataset"

# Create directories if they don't exist
for dir_path in [DATA_DIR, MODELS_DIR, REPORTS_DIR]:
    dir_path.mkdir(exist_ok=True)
    (dir_path / "raw").mkdir(exist_ok=True)
    (dir_path / "processed").mkdir(exist_ok=True)

# ============================================================================
# DATA CONFIGURATION
# ============================================================================
ASSETS = {
    "gold": {
        "name": "XAU/USD",
        "files": {
            "5m": GOLD_DATASET_DIR / "Gold_5m_Candlestick.csv",
            "15m": GOLD_DATASET_DIR / "Gold_15m_Candlestick_4Y.csv",
            "30m": GOLD_DATASET_DIR / "Gold_30m_Candlestick.csv",
            "1h": GOLD_DATASET_DIR / "Gold_1h_Candlestick.csv"
        }
    },
    "silver": {
        "name": "XAG/USD",
        "files": {
            "5m": SILVER_DATASET_DIR / "Silver_5m_Candlestick.csv",
            "15m": SILVER_DATASET_DIR / "Silver_15m_Candlestick.csv",
            "30m": SILVER_DATASET_DIR / "Silver_30m_Candlestick.csv",
            "1h": SILVER_DATASET_DIR / "Silver_1h_Candlestick.csv"
        }
    }
}

# ============================================================================
# BASELINE PARAMETERS (FROM YOUR EXISTING MODEL)
# ============================================================================
BASELINE_CONFIG = {
    "primary_timeframe": "15m",
    "label_params": {
        "take_profit_pct": 0.0015,  # 0.15% (adjusted for Silver volatility - was 0.0045 for Gold)
        "stop_loss_pct": 0.0005,     # 0.05% (adjusted for Silver volatility - was 0.0015 for Gold)
        "max_bars": 6                # Look ahead 6 bars (90 minutes on 15m)
    },
    "session_filter": {
        "enabled": True,
        "start_time": "08:00",  # London open
        "end_time": "17:00"     # NY close
    },
    "train_split": {
        "train": 0.70,
        "val": 0.15,
        "test": 0.15
    },
    "xgboost_params": {
        "n_estimators": 1500,
        "objective": "binary:logistic",
        "eval_metric": "logloss",
        "early_stopping_rounds": 50,
        "random_state": 42
    }
}

# ============================================================================
# ASSET-SPECIFIC PARAMETERS
# ============================================================================
# Gold has higher volatility, so higher thresholds work
GOLD_LABEL_PARAMS = {
    "take_profit_pct": 0.0045,   # 0.45% for Gold (higher volatility)
    "stop_loss_pct": 0.0015,     # 0.15% for Gold
    "max_bars": 6                # Look ahead 6 bars (90 minutes on 15m)
}

# Silver has lower volatility, needs tighter thresholds to generate positive labels
SILVER_LABEL_PARAMS = {
    "take_profit_pct": 0.003,    # 0.3% for Silver (training labels)
    "stop_loss_pct": 0.001,      # 0.1% for Silver (training labels)
    "max_bars": 6                # Look ahead 6 bars (90 minutes on 15m)
}

# Display TP/SL — realistic trade levels shown on dashboard (NOT training labels)
GOLD_TRADE_PARAMS = {
    "take_profit_pct": 0.01,     # 1.0% — realistic for gold daily range
    "stop_loss_pct": 0.005,      # 0.5%
}
SILVER_TRADE_PARAMS = {
    "take_profit_pct": 0.015,    # 1.5% — silver is more volatile
    "stop_loss_pct": 0.0075,     # 0.75%
}

# ============================================================================
# FEATURE ENGINEERING CONFIGURATION
# ============================================================================
FEATURE_CONFIG = {
    # Volume-based features (from your existing model)
    "volume_features": {
        "windows": [4, 16, 96],  # 1h, 4h, 24h on 15m
        "vwap_deviation": True,
        "cvd": True,              # Cumulative Volume Delta
        "imbalance": True,        # Buy/Sell imbalance
        "wick_ratio": True
    },
    
    # Smart Money Concepts (NEW)
    "smc_features": {
        "fair_value_gaps": True,
        "break_of_structure": True,
        "liquidity_sweeps": True,
        "order_blocks": True,
        "premium_discount": True,
        "fvg_threshold": 0.0005,  # 0.05% minimum gap
        "bos_lookback": 20        # Bars to look back for structure
    },
    
    # Multi-timeframe features (NEW)
    "multi_timeframe": {
        "enabled": True,
        "timeframes": ["5m", "15m", "30m", "1h"],
        "primary": "15m",
        "features_from_higher_tf": [
            "trend", "volatility", "support_resistance",
            "rsi", "ema_20", "ema_50"
        ]
    },
    
    # Technical indicators
    "technical": {
        "rsi_periods": [14],
        "ema_periods": [20, 50, 200],
        "atr_period": 14,
        "bollinger_period": 20,
        "bollinger_std": 2.0
    }
}

# ============================================================================
# BACKTESTING CONFIGURATION
# ============================================================================
BACKTEST_CONFIG = {
    "initial_capital": 1000.0,
    "risk_per_trade_usd": 3.0,
    "commission_pct": 0.0001,  # 0.01% per trade
    "slippage_pct": 0.0002,    # 0.02% slippage
    "max_positions": 1,         # Single position at a time
    "respect_session_filter": True,
    "walk_forward": {
        "enabled": True,
        "train_window_months": 12,
        "test_window_months": 3,
        "step_months": 3
    }
}

# ============================================================================
# MODEL CONFIGURATION
# ============================================================================
MODEL_CONFIG = {
    "baseline_model_path": PROJECT_ROOT / "xau_ny_london_15m.pkl",
    "gpp_model_path": PROJECT_ROOT / "gpp_model.pkl",
    "enhanced_model_path": MODELS_DIR / "enhanced_15m.pkl",
    "ensemble_size": 5,  # Number of models in ensemble
    "threshold_calibration": True,
    "target_recall": 0.50  # Target recall for threshold tuning
}

# ============================================================================
# SHAP CONFIGURATION
# ============================================================================
SHAP_CONFIG = {
    "enabled": True,
    "sample_size": 1000,  # Number of samples for SHAP computation
    "plot_top_n": 20,     # Top N features to plot
    "save_plots": True,
    "plots_dir": REPORTS_DIR / "shap_plots"
}

# ============================================================================
# API CONFIGURATION
# ============================================================================
API_CONFIG = {
    "host": "0.0.0.0",
    "port": 5000,
    "debug": False,
    "cors_enabled": True
}

# ============================================================================
# DASHBOARD CONFIGURATION
# ============================================================================
DASHBOARD_CONFIG = {
    "title": "MetalMind - SMC Trading Signals",
    "update_interval_sec": 60,
    "chart_history_bars": 500,
    "show_baseline_comparison": True
}

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": PROJECT_ROOT / "ml_signals.log",
    "console": True
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def get_asset_file(asset: str, timeframe: str) -> Path:
    """Get file path for specific asset and timeframe."""
    return ASSETS[asset]["files"][timeframe]

def get_label_params(asset: str = "gold"):
    """Get label generation parameters specific to the asset."""
    if asset.lower() == "silver":
        return SILVER_LABEL_PARAMS
    else:  # Default to Gold
        return GOLD_LABEL_PARAMS

def get_session_times():
    """Get trading session filter times."""
    return BASELINE_CONFIG["session_filter"]

def get_xgboost_params():
    """Get XGBoost hyperparameters."""
    return BASELINE_CONFIG["xgboost_params"]

# ============================================================================
# DATA QUALITY GATE (etl/guards/data_quality_gate.py)
# Extends DataQualityTransformer — only the gaps it doesn't cover.
# ============================================================================
DATA_QUALITY_GATE_CONFIG = {
    "max_price_change_pct": 0.10,      # Drop candle if |close-prev_close|/prev_close > 10%
    "min_rows_required": 50,           # Skip run entirely if fewer rows survive
    "enabled": True,
}

# ============================================================================
# ALERT RISK GATE (etl/guards/alert_risk_gate.py)
# Deterministic gate run at the live alert call site (api/app/main.py:688).
# ============================================================================
ALERT_RISK_GATE_CONFIG = {
    "enabled": True,
    "min_alert_interval_min": 30,       # Cooldown per asset — biggest ROI
    "suppress_weekends": True,
    "session_start_utc": "07:00",       # London open (UTC)
    "session_end_utc": "21:00",         # NY close (UTC)
    "enforce_session": False,           # Off by default — opt-in
    "max_atr_multiplier": 2.0,          # ATR > 2x 20-bar avg => suppress
    "enforce_volatility": False,        # Off by default — see AD7
}

# ============================================================================
# SIGNAL REASONER AGENT (etl/agents/signal_reasoner.py)
# One LLM call, OpenAI-compatible. Backtest-safe by construction (AD4).
# ============================================================================
SIGNAL_REASONER_CONFIG = {
    "enabled_env_var": "ML_AGENT_ENABLED",        # "true"/"false"; default false
    "api_key_env_var": "NVIDIA_API_KEY",
    "api_url": "https://integrate.api.nvidia.com/v1/chat/completions",
    "model": "nvidia/nemotron-3-ultra-550b-a55b",
    "timeout_env_var": "ML_AGENT_TIMEOUT_SEC",    # default 8 seconds
    "default_timeout_sec": 8,
    "temperature": 0.1,
    "max_tokens": 200,
    "fail_open": True,                              # AD5 — approve if LLM unavailable
}
