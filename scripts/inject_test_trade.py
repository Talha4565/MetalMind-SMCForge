"""Inject a test BUY trade with TP/SL into the prediction log."""
import os
os.environ['SECRET_KEY'] = 'x'
os.environ['JWT_SECRET_KEY'] = 'x'
os.environ['REFRESH_SECRET_KEY'] = 'x'

import json
from pathlib import Path
from datetime import datetime

log_dir = Path('/app/reports/predictions')
today = datetime.now().strftime('%Y%m%d')
log_file = log_dir / f'predictions_{today}.jsonl'

record = {
    'timestamp': datetime.now().isoformat(),
    'asset': 'gold',
    'signal': 1,
    'signal_text': 'BUY',
    'confidence': 0.72,
    'price': 4028.0,
    'tp_price': 4046.23,
    'sl_price': 4021.94,
    'shap_values': [],
    'model_version': 'v5_test',
    'actual_outcome': None,
    'actual_pnl': None,
    'outcome_checked_at': None,
}

with open(log_file, 'a') as f:
    f.write(json.dumps(record) + '\n')

print(f'Test BUY logged: entry=$4028 TP=$4046.23 SL=$4021.94')
print(f'Current gold price: ~$4028 (close to SL)')
