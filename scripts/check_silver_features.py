import pickle
from pathlib import Path

silver = Path(r"C:\Users\Talha\ml-signals\models\silver_enhanced_15m.pkl")
with open(silver, "rb") as f:
    model = pickle.load(f)

features = list(model.feature_names_in_) if hasattr(model, "feature_names_in_") else []
trend_cols = [f for f in features if "trend" in f.lower() or "ema" in f.lower() or "adx" in f.lower() or "rsi" in f.lower() or "macd" in f.lower()]
print(f"Total features: {len(features)}")
print(f"Trend/indicator cols: {trend_cols}")
print(f"Has trend_ema_cross: {'trend_ema_cross' in features}")
print(f"Has adx_14: {'adx_14' in features}")
print(f"Has rsi_14: {'rsi_14' in features}")
print()
print("Last 10 features:")
for f in features[-10:]:
    print(f"  {f}")
