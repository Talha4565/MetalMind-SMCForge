"""
Risk Manager — Enforces position sizing, daily/monthly stops, and trade logging.
Silver T=0.7 system: 0.5% risk/trade, 2% daily stop, 5% monthly stop.
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta
from threading import Lock

logger = logging.getLogger(__name__)

CONFIG = {
    'account_size': 5000,
    'risk_per_trade': 0.005,       # 0.5%
    'daily_max_loss': 0.02,        # 2%
    'monthly_max_dd': 0.05,        # 5%
    'min_threshold': 0.7,          # Only take T>=0.7 signals
    'sl_atr_mult': 1.5,
    'tp_atr_mult': 3.0,
    'max_trades_per_day': 20,
    'cooldown_after_loss_streak': 3,  # Pause after 3 consecutive losses
}


class RiskManager:
    """Enforces risk rules and tracks PnL."""

    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or Path(__file__).parent.parent.parent / 'reports' / 'risk'
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._daily_pnl = 0.0
        self._monthly_pnl = 0.0
        self._daily_trades = 0
        self._consecutive_losses = 0
        self._today = self._date_str()
        self._month = self._month_str()
        self._trade_log = []
        self._load_state()

    def _date_str(self):
        return datetime.now(timezone.utc).strftime('%Y-%m-%d')

    def _month_str(self):
        return datetime.now(timezone.utc).strftime('%Y-%m')

    def _load_state(self):
        state_file = self.data_dir / 'state.json'
        if state_file.exists():
            try:
                state = json.loads(state_file.read_text())
                if state.get('date') == self._date_str():
                    self._daily_pnl = state.get('daily_pnl', 0)
                    self._daily_trades = state.get('daily_trades', 0)
                    self._consecutive_losses = state.get('consecutive_losses', 0)
                if state.get('month') == self._month_str():
                    self._monthly_pnl = state.get('monthly_pnl', 0)
            except Exception:
                pass

    def _save_state(self):
        state = {
            'date': self._today,
            'month': self._month,
            'daily_pnl': self._daily_pnl,
            'monthly_pnl': self._monthly_pnl,
            'daily_trades': self._daily_trades,
            'consecutive_losses': self._consecutive_losses,
        }
        (self.data_dir / 'state.json').write_text(json.dumps(state, indent=2))

    def _reset_daily_if_needed(self):
        today = self._date_str()
        if today != self._today:
            self._today = today
            self._daily_pnl = 0.0
            self._daily_trades = 0
            self._consecutive_losses = 0

    def _reset_monthly_if_needed(self):
        month = self._month_str()
        if month != self._month:
            self._month = month
            self._monthly_pnl = 0.0

    def calculate_lot_size(self, atr: float, symbol: str = 'XAGUSD') -> dict:
        """Calculate position size based on ATR and risk parameters."""
        account = CONFIG['account_size']
        risk_amount = account * CONFIG['risk_per_trade']
        sl_pips = atr * CONFIG['sl_atr_mult']

        if symbol == 'XAGUSD':
            pip_value = 1  # $1 per pip per 0.01 lot (simplified)
            lot_size = risk_amount / (sl_pips * 100) if sl_pips > 0 else 0
        elif symbol == 'XAUUSD':
            pip_value = 1
            lot_size = risk_amount / (sl_pips * 100) if sl_pips > 0 else 0
        else:
            lot_size = 0

        lot_size = round(lot_size, 2)

        return {
            'symbol': symbol,
            'atr': round(atr, 2),
            'sl_pips': round(sl_pips, 2),
            'tp_pips': round(atr * CONFIG['tp_atr_mult'], 2),
            'lot_size': lot_size,
            'risk_amount': round(risk_amount, 2),
            'potential_loss': round(risk_amount, 2),
            'potential_profit': round(risk_amount * 2, 2),
            'risk_reward': '1:2',
        }

    def can_trade(self) -> dict:
        """Check if trading is allowed right now."""
        self._reset_daily_if_needed()
        self._reset_monthly_if_needed()

        reasons = []

        # Daily stop
        daily_stop = CONFIG['account_size'] * CONFIG['daily_max_loss']
        if self._daily_pnl <= -daily_stop:
            reasons.append(f'Daily stop hit: ${self._daily_pnl:.2f} / -${daily_stop:.2f}')

        # Monthly stop
        monthly_stop = CONFIG['account_size'] * CONFIG['monthly_max_dd']
        if self._monthly_pnl <= -monthly_stop:
            reasons.append(f'Monthly stop hit: ${self._monthly_pnl:.2f} / -${monthly_stop:.2f}')

        # Daily trade limit
        if self._daily_trades >= CONFIG['max_trades_per_day']:
            reasons.append(f'Daily trade limit: {self._daily_trades}/{CONFIG["max_trades_per_day"]}')

        # Consecutive loss cooldown
        if self._consecutive_losses >= CONFIG['cooldown_after_loss_streak']:
            reasons.append(f'Consecutive loss cooldown: {self._consecutive_losses} losses')

        return {
            'allowed': len(reasons) == 0,
            'reasons': reasons,
            'daily_pnl': round(self._daily_pnl, 2),
            'monthly_pnl': round(self._monthly_pnl, 2),
            'daily_trades': self._daily_trades,
            'consecutive_losses': self._consecutive_losses,
        }

    def log_trade(self, signal: str, prob: float, entry: float, atr: float,
                  pnl: float, sl_hit: bool, tp_hit: bool):
        """Log a completed trade."""
        with self._lock:
            self._reset_daily_if_needed()
            self._reset_monthly_if_needed()

            self._daily_pnl += pnl
            self._monthly_pnl += pnl
            self._daily_trades += 1

            if pnl < 0:
                self._consecutive_losses += 1
            else:
                self._consecutive_losses = 0

            trade = {
                'time': datetime.now(timezone.utc).isoformat(),
                'signal': signal,
                'prob': round(prob, 4),
                'entry': round(entry, 2),
                'atr': round(atr, 2),
                'pnl': round(pnl, 2),
                'sl_hit': sl_hit,
                'tp_hit': tp_hit,
                'daily_pnl': round(self._daily_pnl, 2),
                'monthly_pnl': round(self._monthly_pnl, 2),
            }
            self._trade_log.append(trade)

            # Keep last 500 trades
            if len(self._trade_log) > 500:
                self._trade_log = self._trade_log[-500:]

            self._save_state()
            self._log_trade_to_file(trade)

    def _log_trade_to_file(self, trade):
        log_file = self.data_dir / f"trades_{self._month}.jsonl"
        with open(log_file, 'a') as f:
            f.write(json.dumps(trade) + '\n')

    def get_status(self) -> dict:
        """Get current risk manager status."""
        self._reset_daily_if_needed()
        self._reset_monthly_if_needed()

        can = self.can_trade()
        daily_stop = CONFIG['account_size'] * CONFIG['daily_max_loss']
        monthly_stop = CONFIG['account_size'] * CONFIG['monthly_max_dd']

        return {
            'account_size': CONFIG['account_size'],
            'risk_per_trade_pct': CONFIG['risk_per_trade'] * 100,
            'risk_per_trade_usd': round(CONFIG['account_size'] * CONFIG['risk_per_trade'], 2),
            'daily_pnl': round(self._daily_pnl, 2),
            'daily_stop': round(-daily_stop, 2),
            'daily_stop_pct': round(self._daily_pnl / CONFIG['account_size'] * 100, 2),
            'monthly_pnl': round(self._monthly_pnl, 2),
            'monthly_stop': round(-monthly_stop, 2),
            'monthly_stop_pct': round(self._monthly_pnl / CONFIG['account_size'] * 100, 2),
            'daily_trades': self._daily_trades,
            'max_daily_trades': CONFIG['max_trades_per_day'],
            'consecutive_losses': self._consecutive_losses,
            'cooldown_threshold': CONFIG['cooldown_after_loss_streak'],
            'can_trade': can['allowed'],
            'block_reasons': can['reasons'],
            'min_threshold': CONFIG['min_threshold'],
            'sl_atr_mult': CONFIG['sl_atr_mult'],
            'tp_atr_mult': CONFIG['tp_atr_mult'],
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }

    def get_weekly_stats(self) -> dict:
        """Get weekly performance stats."""
        trades_file = self.data_dir / f"trades_{self._month}.jsonl"
        if not trades_file.exists():
            return {'trades': 0, 'wins': 0, 'losses': 0, 'win_rate': 0, 'pf': 0, 'pnl': 0}

        trades = []
        for line in trades_file.read_text().strip().split('\n'):
            if line:
                try:
                    trades.append(json.loads(line))
                except:
                    pass

        # Last 7 days
        cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        recent = [t for t in trades if t.get('time', '') >= cutoff]

        if not recent:
            return {'trades': 0, 'wins': 0, 'losses': 0, 'win_rate': 0, 'pf': 0, 'pnl': 0}

        wins = [t for t in recent if t['pnl'] > 0]
        losses = [t for t in recent if t['pnl'] < 0]

        gross_profit = sum(t['pnl'] for t in wins) if wins else 0
        gross_loss = abs(sum(t['pnl'] for t in losses)) if losses else 0.01

        return {
            'period': '7 days',
            'trades': len(recent),
            'wins': len(wins),
            'losses': len(losses),
            'win_rate': round(len(wins) / len(recent) * 100, 1),
            'profit_factor': round(gross_profit / gross_loss, 2),
            'total_pnl': round(sum(t['pnl'] for t in recent), 2),
            'avg_win': round(sum(t['pnl'] for t in wins) / len(wins), 2) if wins else 0,
            'avg_loss': round(sum(t['pnl'] for t in losses) / len(losses), 2) if losses else 0,
        }


risk_manager = RiskManager()
