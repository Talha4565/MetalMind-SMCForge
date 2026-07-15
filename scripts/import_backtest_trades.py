"""
Import backtest trades into prediction logger for trade log display.
Reads backtest results and converts trades to prediction log format.
"""
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))


def import_backtest_trades(asset: str = 'gold'):
    """Import backtest trades into prediction log format."""

    # Read backtest results
    backtest_file = Path(f'C:/Users/Talha/ml-signals/reports/backtest_results/{asset}_backtest.json')
    if not backtest_file.exists():
        print(f"Backtest file not found: {backtest_file}")
        return

    with open(backtest_file) as f:
        data = json.load(f)

    trades = data.get('trades', [])
    print(f"Found {len(trades)} trades in {asset} backtest")

    # Convert trades to prediction log format
    predictions = []
    for i, trade in enumerate(trades):
        # Determine signal from direction
        if trade['direction'] == 'long':
            signal = 1
            signal_text = 'BUY'
        else:
            signal = -1
            signal_text = 'SELL'

        # Calculate TP/SL prices from trade data
        entry_price = trade['entry_price']
        hit_tp = trade.get('hit_tp', False)
        hit_sl = trade.get('hit_sl', False)

        # Calculate TP/SL based on config
        tp_pct = 0.0045 if asset == 'gold' else 0.003
        sl_pct = 0.0015 if asset == 'gold' else 0.001

        tp_price = round(entry_price * (1 + tp_pct), 2)
        sl_price = round(entry_price * (1 - sl_pct), 2)

        # Determine outcome
        if hit_tp:
            outcome = 'WIN'
        elif hit_sl:
            outcome = 'LOSS'
        elif trade['pnl_usd'] > 0:
            outcome = 'WIN'
        else:
            outcome = 'LOSS'

        # Use original entry_time but ensure it's recent enough to display
        # Backtest trades from May-June need to be mapped to recent dates
        original_time = trade['entry_time']
        entry_dt = datetime.fromisoformat(original_time)

        # If the trade is older than 30 days, map it to a recent date
        now = datetime.now()
        if (now - entry_dt).days > 30:
            # Map to last 30 days, preserving time of day
            days_ago = 30 - (i % 30)  # Spread across last 30 days
            mapped_time = (now - timedelta(days=days_ago)).replace(
                hour=entry_dt.hour, minute=entry_dt.minute, second=entry_dt.second
            )
            timestamp = mapped_time.isoformat()
        else:
            timestamp = original_time

        # Create prediction log entry
        pred = {
            'timestamp': timestamp,
            'asset': asset,
            'signal': signal,
            'signal_text': signal_text,
            'confidence': 0.75,  # Backtest trades are assumed high confidence
            'price': round(entry_price, 2),
            'tp_price': tp_price,
            'sl_price': sl_price,
            'shap_values': [],
            'model_version': 'backtest_v1',
            'actual_outcome': outcome,
            'actual_pnl': round(trade['pnl_pct'] * 100, 2),  # Convert to percentage
            'outcome_checked_at': trade['exit_time'],
            'is_backtest': True,
        }
        predictions.append(pred)

    # Write to prediction log file
    output_dir = Path('C:/Users/Talha/ml-signals/reports/predictions')
    output_dir.mkdir(parents=True, exist_ok=True)

    # Use today's date for the import
    today = datetime.now().strftime('%Y%m%d')
    output_file = output_dir / f'predictions_{today}.jsonl'

    # Read existing predictions
    existing = []
    if output_file.exists():
        with open(output_file) as f:
            for line in f:
                if line.strip():
                    existing.append(json.loads(line))

    # Filter out existing backtest imports
    existing = [p for p in existing if p.get('model_version') != 'backtest_v1']

    # Combine
    all_predictions = existing + predictions

    # Sort by timestamp
    all_predictions.sort(key=lambda r: r.get('timestamp', ''), reverse=True)

    # Write back
    with open(output_file, 'w') as f:
        for pred in all_predictions:
            f.write(json.dumps(pred) + '\n')

    print(f"Imported {len(predictions)} backtest trades to {output_file.name}")
    print(f"Total predictions in file: {len(all_predictions)}")

    # Print summary
    wins = sum(1 for p in predictions if p['actual_outcome'] == 'WIN')
    losses = sum(1 for p in predictions if p['actual_outcome'] == 'LOSS')
    print(f"Wins: {wins} | Losses: {losses} | Win Rate: {wins/(wins+losses)*100:.1f}%")

    return predictions


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Import backtest trades')
    parser.add_argument('--asset', choices=['gold', 'silver', 'all'], default='all')
    args = parser.parse_args()

    assets = ['gold', 'silver'] if args.asset == 'all' else [args.asset]

    for asset in assets:
        print(f"\n{'='*60}")
        print(f"IMPORTING {asset.upper()} BACKTEST TRADES")
        print(f"{'='*60}")
        import_backtest_trades(asset)
