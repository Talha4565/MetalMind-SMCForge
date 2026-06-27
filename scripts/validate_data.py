"""Quick data validation before training."""
import sys
sys.path.insert(0, r'C:\Users\Talha\ml-signals')

from data.loaders import load_asset_data, train_val_test_split
from features.pipeline import engineer_all_features

print('=' * 60)
print('DATA VALIDATION')
print('=' * 60)

for asset in ['gold', 'silver']:
    print(f'\n--- {asset.upper()} ---')
    df = load_asset_data(asset=asset, primary_tf='15m', session_filter=True)
    print(f'Loaded: {len(df)} rows, {df.index.min()} to {df.index.max()}')
    print(f'Columns: {len(df.columns)}')
    print(f'OHLC sample:\n{df[["open","high","low","close","volume"]].head(3)}')

    df_eng = engineer_all_features(df, add_labels=True, asset=asset)
    print(f'After features: {len(df_eng)} rows, {len(df_eng.columns)} cols')
    targets = df_eng['target'].value_counts().to_dict()
    print(f'Target dist: {targets}')
    print(f'NaN count: {df_eng.isnull().sum().sum()}')

    train, val, test = train_val_test_split(df_eng)
    print(f'Split: train={len(train)}, val={len(val)}, test={len(test)}')
    if len(train) > 0:
        print(f'Label balance (train mean): {train["target"].mean():.3f}')
    print(f'Train range: {train.index.min()} to {train.index.max()}')
    print(f'Test range:  {test.index.min()} to {test.index.max()}')

print('\n' + '=' * 60)
print('VALIDATION COMPLETE')
print('=' * 60)
