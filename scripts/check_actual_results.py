import json
from pathlib import Path

# Check actual trade outcomes
outcomes_file = Path('reports/learning/trade_outcomes.jsonl')
if outcomes_file.exists():
    outcomes = []
    for line in outcomes_file.read_text().splitlines():
        if line.strip():
            outcomes.append(json.loads(line))
    print(f'Total outcomes: {len(outcomes)}')
    wins = sum(1 for o in outcomes if o.get('outcome') == 'WIN')
    losses = sum(1 for o in outcomes if o.get('outcome') == 'LOSS')
    pending = sum(1 for o in outcomes if o.get('outcome') not in ('WIN', 'LOSS'))
    print(f'Wins: {wins}, Losses: {losses}, Pending: {pending}')
    pnls = [o.get('pnl', 0) for o in outcomes]
    print(f'Total PnL: ${sum(pnls):,.2f}')
    if outcomes:
        print(f'Avg PnL per trade: ${sum(pnls)/len(pnls):,.2f}')
else:
    print('No outcomes file found')

# Check prediction logs
pred_dir = Path('reports/predictions')
if pred_dir.exists():
    pred_files = sorted(pred_dir.glob('predictions_*.jsonl'))
    print(f'\nPrediction files: {len(pred_files)}')
    total_preds = 0
    signals = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
    for pf in pred_files:
        lines = pf.read_text().splitlines()
        total_preds += len(lines)
        for line in lines:
            if line.strip():
                rec = json.loads(line)
                sig = rec.get('signal', 0)
                if sig == 1: signals['BUY'] += 1
                elif sig == -1: signals['SELL'] += 1
                else: signals['HOLD'] += 1
    print(f'Total predictions across all files: {total_preds}')
    print(f'Signal distribution: {signals}')

# Check backtest results
bt_dir = Path('reports/backtest_results')
if bt_dir.exists():
    latest = bt_dir / 'latest.json'
    if latest.exists():
        data = json.loads(latest.read_text())
        m = data.get('metrics', {})
        print(f'\nLatest backtest: {m.get("n_trades", 0)} trades, win_rate={m.get("win_rate", 0):.2%}, total_return=${m.get("total_return_usd", 0):,.2f}')
