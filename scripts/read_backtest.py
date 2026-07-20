"""Read backtest results and prediction logs."""
import json
from pathlib import Path

# Read gold backtest
with open('C:/Users/Talha/ml-signals/reports/backtest_results/gold_backtest.json') as f:
    gold = json.load(f)

print('=' * 70)
print('GOLD BACKTEST RESULTS')
print('=' * 70)
print(f"Trades: {gold['summary']['n_trades']}")
print(f"Win Rate: {gold['summary']['win_rate']*100:.1f}%")
print(f"Profit Factor: {gold['summary']['profit_factor']:.2f}")
print(f"Total Return: ${gold['summary']['total_return_usd']:.2f}")
print(f"Sharpe Ratio: {gold['summary']['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {gold['summary']['max_drawdown_pct']*100:.2f}%")
print()

print('SAMPLE TRADES:')
for i, t in enumerate(gold['trades'][:5]):
    print(f"  {i+1}. {t['entry_time']} -> {t['exit_time']}")
    print(f"     Entry: ${t['entry_price']:.2f} | Exit: ${t['exit_price']:.2f}")
    print(f"     Dir: {t['direction']} | PnL: ${t['pnl_usd']:.2f} | TP: {t['hit_tp']} | SL: {t['hit_sl']}")
    print()

# Read silver backtest
with open('C:/Users/Talha/ml-signals/reports/backtest_results/silver_backtest.json') as f:
    silver = json.load(f)

print('=' * 70)
print('SILVER BACKTEST RESULTS')
print('=' * 70)
print(f"Trades: {silver['summary']['n_trades']}")
print(f"Win Rate: {silver['summary']['win_rate']*100:.1f}%")
print(f"Profit Factor: {silver['summary']['profit_factor']:.2f}")
print(f"Total Return: ${silver['summary']['total_return_usd']:.2f}")
print()

# Read prediction logs
print('=' * 70)
print('PREDICTION LOGS (today)')
print('=' * 70)
pred_file = Path('C:/Users/Talha/ml-signals/reports/predictions/predictions_20260714.jsonl')
if pred_file.exists():
    lines = pred_file.read_text().splitlines()
    print(f"Total predictions today: {len(lines)}")
    # Count signals
    signals = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
    for line in lines:
        pred = json.loads(line)
        sig = pred.get('signal_text', 'HOLD')
        signals[sig] = signals.get(sig, 0) + 1
    print(f"Signal distribution: {signals}")
    print()
    print("Last 3 predictions:")
    for line in lines[-3:]:
        pred = json.loads(line)
        print(f"  {pred['timestamp']}: {pred['signal_text']} @ ${pred['price']:.2f} (conf: {pred['confidence']*100:.1f}%)")
        print(f"    TP: ${pred.get('tp_price', 'N/A')} | SL: ${pred.get('sl_price', 'N/A')}")
