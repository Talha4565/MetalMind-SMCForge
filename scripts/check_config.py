import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import BACKTEST_CONFIG, get_label_params

print('Backtest config:')
print(f'  Initial capital: ${BACKTEST_CONFIG["initial_capital"]:,.0f}')
print(f'  Risk per trade: ${BACKTEST_CONFIG["risk_per_trade_usd"]}')
print(f'  Commission: {BACKTEST_CONFIG["commission_pct"]*100:.2f}%')
print(f'  Slippage: {BACKTEST_CONFIG["slippage_pct"]*100:.2f}%')

lp = get_label_params('gold')
print(f'  TP%: {lp["take_profit_pct"]*100:.2f}%')
print(f'  SL%: {lp["stop_loss_pct"]*100:.2f}%')
print(f'  Max bars: {lp["max_bars"]}')

# Calculate max possible return per trade
tp = lp['take_profit_pct']
sl = lp['stop_loss_pct']
risk = BACKTEST_CONFIG['risk_per_trade_usd']
commission = BACKTEST_CONFIG['commission_pct']
slippage = BACKTEST_CONFIG['slippage_pct']
capital = BACKTEST_CONFIG['initial_capital']

print(f'\nPer trade economics:')
print(f'  Risk: ${risk} ({risk/capital*100:.2f}% of capital)')
print(f'  Max win per trade: ${risk * tp / sl:.2f} (if TP hit)')
print(f'  Max loss per trade: ${risk:.2f} (if SL hit)')
print(f'  Round-trip cost: {(commission + slippage) * 2 * 100:.2f}% = ${capital * (commission + slippage) * 2:.2f}')
