import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
import pickle
from data.loaders import load_asset_data
from features.pipeline import engineer_all_features
from features.v4_features import compute_v4_features
from backtesting.engine import BacktestEngine

# Load data
print('Loading data...')
df = load_asset_data(asset='gold', primary_tf='15m', session_filter=False)
df = engineer_all_features(df, add_labels=True, asset='gold')
df = compute_v4_features(df)

# Load V4 model
with open('models/gold_regression_system.pkl', 'rb') as f:
    model_data = pickle.load(f)

features = model_data['features']
model = model_data['direction_model']

# Prepare features
X = df[features]
valid = X.notna().all(axis=1)
X_clean = X[valid]
df_clean = df[valid]

# Predict
proba = model.predict_proba(X_clean)[:, 1]
confidence = np.maximum(proba, 1 - proba)

# Signal: BUY when confidence >= 0.65 and proba >= 0.5
signals = np.zeros(len(X_clean), dtype=int)
for i in range(len(X_clean)):
    if confidence[i] >= 0.65 and proba[i] >= 0.5:
        signals[i] = 1

print(f'Data range: {df_clean.index.min()} to {df_clean.index.max()}')
print(f'Total bars: {len(df_clean)}')
print(f'Signals: {signals.sum()} BUY out of {len(signals)} bars ({signals.sum()/len(signals)*100:.1f}%)')

# Run backtest with $5,000
engine = BacktestEngine(asset='gold', initial_capital=5000)
results = engine.run_backtest(df_clean, signals)
m = results.get('metrics', {})

print(f'')
print(f'=== BACKTEST: $5,000 CAPITAL, V4 MODEL, 65% CONFIDENCE ===')
print(f'Period: {df_clean.index.min().strftime("%Y-%m-%d")} to {df_clean.index.max().strftime("%Y-%m-%d")}')
months = (df_clean.index.max() - df_clean.index.min()).days / 30
print(f'Duration: {months:.1f} months')
print(f'')
print(f'Trades:       {m.get("n_trades", 0)}')
print(f'Win Rate:     {m.get("win_rate", 0):.2%}')
print(f'Profit Factor:{m.get("profit_factor", 0):.2f}')
print(f'Total Return: ${m.get("total_return_usd", 0):,.2f} ({m.get("total_return_pct", 0):.1f}%)')
print(f'Sharpe Ratio: {m.get("sharpe_ratio", 0):.2f}')
print(f'Max Drawdown: {m.get("max_drawdown_pct", 0):.2f}%')
print(f'Final Equity: ${5000 * (1 + m.get("total_return_pct", 0) / 100):,.2f}')
