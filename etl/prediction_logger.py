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
        tp_distance: float = None,
        sl_distance: float = None,
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
            'shap_values': shap_values[:5] if shap_values else [],
            'model_version': model_version or 'v4',
            'tp_distance': round(tp_distance, 4) if tp_distance is not None else None,
            'sl_distance': round(sl_distance, 4) if sl_distance is not None else None,
            'actual_outcome': None,
            'actual_pnl': None,
            'outcome_checked_at': None,
        }
        
        # Append to daily JSONL file
        with open(self.current_file, 'a') as f:
            f.write(json.dumps(record) + '\n')
        
        logger.info(f"Logged prediction: {signal_text} {asset} @ ${price:.2f} ({confidence:.1%}) TP={tp_distance} SL={sl_distance}")
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
    
    def check_outcomes(self, current_prices: Dict[str, float], tp_pct: float = 0.005, sl_pct: float = 0.003):
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
        """Get summary of recent predictions."""
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
                    summary['total_predictions'] += 1
                    
                    if record['signal'] == 1:
                        summary['buy_signals'] += 1
                    elif record['signal'] == -1:
                        summary['sell_signals'] += 1
                    else:
                        summary['hold_signals'] += 1
                    
                    total_confidence += record['confidence']
                    
                    if record['actual_outcome']:
                        summary['evaluated'] += 1
                        if 'WIN' in record['actual_outcome']:
                            summary['wins'] += 1
                        elif 'LOSS' in record['actual_outcome']:
                            summary['losses'] += 1
        
        if summary['total_predictions'] > 0:
            summary['avg_confidence'] = round(total_confidence / summary['total_predictions'], 4)
        
        return summary
