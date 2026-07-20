"""Show trade log data from API."""
import json
import urllib.request

# Fetch trade log
url = 'http://localhost:5000/api/predictions/history?days=30&limit=20'
with urllib.request.urlopen(url) as resp:
    data = json.loads(resp.read())

print('=' * 80)
print('TRADE LOG - Dashboard Data')
print('=' * 80)
print()
print(f"Summary:")
print(f"  Total Trades: {data['summary']['total_predictions']}")
print(f"  BUY Signals:  {data['summary']['buy_signals']}")
print(f"  SELL Signals: {data['summary']['sell_signals']}")
print(f"  Wins:         {data['summary']['wins']}")
print(f"  Losses:       {data['summary']['losses']}")
print(f"  Win Rate:     {data['summary']['wins']/(data['summary']['wins']+data['summary']['losses'])*100:.1f}%")
print()
print('=' * 80)
print(f"{'Time':<18} {'Signal':<6} {'Entry':>10} {'TP':>10} {'SL':>10} {'Outcome':<6} {'PnL':>8}")
print('-' * 80)

for p in data['predictions'][:20]:
    ts = p['timestamp'][:16] if p.get('timestamp') else 'N/A'
    signal = p.get('signal_text', 'N/A')
    price = f"${p['price']:.2f}" if p.get('price') else 'N/A'
    tp = f"${p['tp_price']:.2f}" if p.get('tp_price') else 'N/A'
    sl = f"${p['sl_price']:.2f}" if p.get('sl_price') else 'N/A'
    outcome = p.get('actual_outcome', 'PENDING') or 'PENDING'
    pnl = f"{p['actual_pnl']:+.2f}%" if p.get('actual_pnl') is not None else 'N/A'

    print(f"{ts:<18} {signal:<6} {price:>10} {tp:>10} {sl:>10} {outcome:<6} {pnl:>8}")

print('=' * 80)
