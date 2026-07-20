"""
Prediction logger — logs every prediction with signal, price, SHAP, and tracks actual outcomes.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class PredictionLogger:
    """Log predictions and track outcomes."""
    
    def __init__(self, log_dir: str = None):
        from config.settings import REPORTS_DIR
        self.log_dir = Path(log_dir) if log_dir else REPORTS_DIR / 'predictions'
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.current_file = self.log_dir / f"predictions_{datetime.now().strftime('%Y%m%d')}.jsonl"
    
    def log_prediction(
        self,
        asset: str,
        signal: int,
        confidence: float,
        price: float,
        shap_values: list = None,
        model_version: str = None,
        tp_price: float = None,
        sl_price: float = None,
    ) -> dict:
        """
        Log a single prediction.
        
        Returns the logged record.
        """
        signal_text = {1: 'BUY', -1: 'SELL', 0: 'HOLD'}.get(signal, 'UNKNOWN')
        
        record = {
            'timestamp': datetime.now().isoformat(),
            'asset': asset,
            'signal': signal,
            'signal_text': signal_text,
            'confidence': round(confidence, 4),
            'price': round(price, 2),
            'tp_price': tp_price,
            'sl_price': sl_price,
            'shap_values': shap_values[:5] if isinstance(shap_values, list) else [],
            'model_version': model_version or 'latest',
            'actual_outcome': None,  # Filled later when price moves
            'actual_pnl': None,
            'outcome_checked_at': None,
        }
        
        # Append to daily JSONL file
        with open(self.current_file, 'a') as f:
            f.write(json.dumps(record) + '\n')
        
        logger.info(f"Logged prediction: {signal_text} {asset} @ ${price:.2f} ({confidence:.1%})")
        return record
    
    def log_batch(self, predictions: List[Dict[str, Any]]):
        """Log multiple predictions at once."""
        for pred in predictions:
            self.log_prediction(
                asset=pred.get('asset', 'unknown'),
                signal=pred.get('signal', 0),
                confidence=pred.get('confidence', 0),
                price=pred.get('price', 0),
                shap_values=pred.get('shap_values', []),
                model_version=pred.get('model_version')
            )
    
    def check_outcomes(self, current_prices: Dict[str, float], tp_pct: float = 0.01, sl_pct: float = 0.005):
        """
        Check actual outcomes for open predictions.
        
        Args:
            current_prices: dict of asset -> current price
            tp_pct: Take profit percentage (0.5% default)
            sl_pct: Stop loss percentage (0.3% default)
        """
        today_file = self.log_dir / f"predictions_{datetime.now().strftime('%Y%m%d')}.jsonl"
        if not today_file.exists():
            return
        
        records = []
        updated = 0
        
        with open(today_file, 'r') as f:
            for line in f:
                record = json.loads(line.strip())
                
                # Only check predictions that haven't been evaluated
                if record['actual_outcome'] is None and record['signal'] != 0:
                    asset = record['asset']
                    entry_price = record['price']
                    signal = record['signal']
                    current_price = current_prices.get(asset)
                    
                    if current_price is None:
                        records.append(record)
                        continue
                    
                    # Calculate if TP or SL was hit
                    if signal == 1:  # BUY
                        pnl_pct = (current_price - entry_price) / entry_price
                    else:  # SELL
                        pnl_pct = (entry_price - current_price) / entry_price
                    
                    if pnl_pct >= tp_pct:
                        record['actual_outcome'] = 'WIN_TP'
                        record['actual_pnl'] = round(pnl_pct * 100, 2)
                        updated += 1
                    elif pnl_pct <= -sl_pct:
                        record['actual_outcome'] = 'LOSS_SL'
                        record['actual_pnl'] = round(pnl_pct * 100, 2)
                        updated += 1
                    elif abs(pnl_pct) > 0.001:  # At least 0.1% movement
                        record['actual_outcome'] = 'WIN' if pnl_pct > 0 else 'LOSS'
                        record['actual_pnl'] = round(pnl_pct * 100, 2)
                        updated += 1
                    
                    if record['actual_outcome']:
                        record['outcome_checked_at'] = datetime.now().isoformat()
                
                records.append(record)
        
        # Rewrite file
        with open(today_file, 'w') as f:
            for record in records:
                f.write(json.dumps(record) + '\n')
        
        if updated:
            logger.info(f"Updated {updated} prediction outcomes")
    
    def get_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get summary of recent predictions (BUY/SELL only, excluding HOLD)."""
        from datetime import timedelta
        
        summary = {
            'total_predictions': 0,
            'buy_signals': 0,
            'sell_signals': 0,
            'hold_signals': 0,
            'evaluated': 0,
            'wins': 0,
            'losses': 0,
            'avg_confidence': 0,
        }
        
        total_confidence = 0
        
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y%m%d')
            log_file = self.log_dir / f"predictions_{date}.jsonl"
            
            if not log_file.exists():
                continue
            
            with open(log_file, 'r') as f:
                for line in f:
                    record = json.loads(line.strip())
                    
                    if record['signal'] == 1:
                        summary['buy_signals'] += 1
                        summary['total_predictions'] += 1
                        total_confidence += record['confidence']
                    elif record['signal'] == -1:
                        summary['sell_signals'] += 1
                        summary['total_predictions'] += 1
                        total_confidence += record['confidence']
                    else:
                        summary['hold_signals'] += 1
                    
                    if record['actual_outcome']:
                        summary['evaluated'] += 1
                        if 'WIN' in record['actual_outcome']:
                            summary['wins'] += 1
                        elif 'LOSS' in record['actual_outcome']:
                            summary['losses'] += 1
        
        if summary['total_predictions'] > 0:
            summary['avg_confidence'] = round(total_confidence / summary['total_predictions'], 4)
        
        return summary

    def get_history(self, days: int = 7, asset: str = None, limit: int = 200) -> List[Dict[str, Any]]:
        """Get prediction log entries for the trade log page."""
        from datetime import timedelta

        records = []
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y%m%d')
            log_file = self.log_dir / f"predictions_{date}.jsonl"

            if not log_file.exists():
                continue

            with open(log_file, 'r') as f:
                for line in f:
                    record = json.loads(line.strip())
                    if asset and record.get('asset', '').lower() != asset.lower():
                        continue
                    records.append(record)

        # Sort newest first, apply limit
        records.sort(key=lambda r: r.get('timestamp', ''), reverse=True)
        return records[:limit]


class ActiveTradeTracker:
    """
    Tracks one active trade per asset with FROZEN TP/SL.
    When a BUY/SELL signal fires at >65% confidence, the entry/tp/sl
    are locked until the trade hits TP, hits SL, or is manually closed.
    No new signals are generated for an asset while it has an active trade.
    """

    def __init__(self):
        self._trades: Dict[str, Dict[str, Any]] = {}

    def has_active(self, asset: str) -> bool:
        return asset in self._trades

    def get_active(self, asset: str) -> Optional[Dict[str, Any]]:
        return self._trades.get(asset)

    def open_trade(self, asset: str, signal: int, confidence: float,
                   entry_price: float, tp_price: float, sl_price: float,
                   shap_values: list = None) -> Dict[str, Any]:
        """Open a new active trade with frozen TP/SL. Overwrites any existing."""
        trade = {
            'asset': asset,
            'signal': signal,
            'signal_text': {1: 'BUY', -1: 'SELL', 0: 'HOLD'}.get(signal, 'UNKNOWN'),
            'confidence': confidence,
            'entry_price': entry_price,
            'tp_price': tp_price,
            'sl_price': sl_price,
            'shap_values': shap_values or [],
            'opened_at': datetime.now().isoformat(),
            'status': 'active',
        }
        self._trades[asset] = trade
        logger.info(f"🔒 ACTIVE TRADE OPENED: {trade['signal_text']} {asset} "
                     f"entry=${entry_price:.2f} tp=${tp_price:.2f} sl=${sl_price:.2f}")
        return trade

    def check_outcome(self, asset: str, current_price: float) -> Optional[Dict[str, Any]]:
        """
        Check if the active trade's TP or SL has been hit.
        Returns a dict with outcome info if the trade resolved, None if still active.
        """
        trade = self._trades.get(asset)
        if not trade or trade['status'] != 'active':
            return None

        entry = trade['entry_price']
        signal = trade['signal']
        tp = trade['tp_price']
        sl = trade['sl_price']

        if signal == 1:  # BUY: price goes UP to hit TP, DOWN to hit SL
            if current_price >= tp:
                pnl_pct = (current_price - entry) / entry
                outcome = 'WIN_TP'
            elif current_price <= sl:
                pnl_pct = (current_price - entry) / entry
                outcome = 'LOSS_SL'
            else:
                return None  # Still active
        else:  # SELL: price goes DOWN to hit TP, UP to hit SL
            if current_price <= tp:
                pnl_pct = (entry - current_price) / entry
                outcome = 'WIN_TP'
            elif current_price >= sl:
                pnl_pct = (entry - current_price) / entry
                outcome = 'LOSS_SL'
            else:
                return None  # Still active

        # Trade resolved — close it
        trade['status'] = 'closed'
        trade['outcome'] = outcome
        trade['actual_pnl'] = round(pnl_pct * 100, 2)
        trade['closed_at'] = datetime.now().isoformat()
        trade['close_price'] = current_price
        del self._trades[asset]

        logger.info(f"✅ ACTIVE TRADE CLOSED: {outcome} {asset} "
                     f"entry=${entry:.2f} exit=${current_price:.2f} pnl={trade['actual_pnl']:+.2f}%")
        return trade

    def all_active(self) -> Dict[str, Dict[str, Any]]:
        return dict(self._trades)
