"""
Outcome Tracker - tracks feature performance over time.
Identifies which features correlate with winning vs losing trades.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class OutcomeTracker:
    """Tracks trade outcomes and feature performance."""

    def __init__(self, data_dir: str = None):
        from config.settings import REPORTS_DIR
        self.data_dir = Path(data_dir) if data_dir else REPORTS_DIR / 'learning'
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.outcomes_file = self.data_dir / 'trade_outcomes.jsonl'
        self.feature_stats_file = self.data_dir / 'feature_stats.json'
        # Dedup: load existing signal IDs so restarts don't re-log everything
        self._seen_ids: set = self._load_existing_ids()

    def _load_existing_ids(self) -> set:
        """Load already-logged signal IDs to prevent duplicate logging on restart."""
        ids = set()
        if self.outcomes_file.exists():
            try:
                for line in self.outcomes_file.read_text().splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        sid = record.get('signal_id')
                        if sid:
                            ids.add(sid)
                    except json.JSONDecodeError:
                        continue
            except Exception:
                pass
        return ids
    
    def log_outcome(self, signal_id: str, asset: str, signal: int,
                   confidence: float, price: float, entry_price: float,
                   outcome: str, pnl: float, features: Dict[str, float] = None):
        """
        Log a trade outcome with its features.
        Skips if signal_id was already logged (dedup across restarts).
        """
        if signal_id in self._seen_ids:
            return  # Already logged — skip
        self._seen_ids.add(signal_id)

        record = {
            'timestamp': datetime.now().isoformat(),
            'signal_id': signal_id,
            'asset': asset,
            'signal': signal,
            'confidence': confidence,
            'entry_price': entry_price,
            'exit_price': price,
            'outcome': outcome,
            'pnl': pnl,
            'features': features or {},
        }
        
        # Append to JSONL file
        with open(self.outcomes_file, 'a') as f:
            f.write(json.dumps(record) + '\n')
        
        # Update feature stats
        self._update_feature_stats(record)
        
        logger.info(f"Outcome logged: {outcome} {asset} PnL={pnl:+.2f}%")
    
    def _update_feature_stats(self, record: Dict[str, Any]):
        """Update aggregate feature statistics."""
        stats = self._load_stats()
        
        features = record.get('features', {})
        outcome = record['outcome']
        
        for feature_name, feature_value in features.items():
            if feature_name not in stats:
                stats[feature_name] = {
                    'win_values': [],
                    'loss_values': [],
                    'win_count': 0,
                    'loss_count': 0,
                }
            
            feat_stats = stats[feature_name]
            
            if outcome == 'WIN':
                feat_stats['win_values'].append(feature_value)
                feat_stats['win_count'] += 1
                # Keep only last 1000 values
                if len(feat_stats['win_values']) > 1000:
                    feat_stats['win_values'] = feat_stats['win_values'][-1000:]
            elif outcome == 'LOSS':
                feat_stats['loss_values'].append(feature_value)
                feat_stats['loss_count'] += 1
                if len(feat_stats['loss_values']) > 1000:
                    feat_stats['loss_values'] = feat_stats['loss_values'][-1000:]
        
        self._save_stats(stats)
    
    def _load_stats(self) -> Dict[str, Any]:
        """Load feature statistics from disk."""
        if self.feature_stats_file.exists():
            return json.loads(self.feature_stats_file.read_text())
        return {}
    
    def _save_stats(self, stats: Dict[str, Any]):
        """Save feature statistics to disk."""
        self.feature_stats_file.write_text(json.dumps(stats, indent=2))
    
    def get_feature_importance(self) -> List[Dict[str, Any]]:
        """
        Calculate feature importance based on win/loss correlation.
        
        Returns:
            List of features sorted by importance (descending)
        """
        stats = self._load_stats()
        
        importance = []
        for feature_name, feat_stats in stats.items():
            win_count = feat_stats.get('win_count', 0)
            loss_count = feat_stats.get('loss_count', 0)
            total = win_count + loss_count
            
            if total < 10:  # Need minimum samples
                continue
            
            win_rate = win_count / total
            
            # Calculate mean values for wins vs losses
            win_values = feat_stats.get('win_values', [])
            loss_values = feat_stats.get('loss_values', [])
            
            win_mean = sum(win_values) / len(win_values) if win_values else 0
            loss_mean = sum(loss_values) / len(loss_values) if loss_values else 0
            
            # Importance = how much the feature discriminates between wins and losses
            discrimination = abs(win_mean - loss_mean) if win_values and loss_values else 0
            
            importance.append({
                'feature': feature_name,
                'win_rate': round(win_rate, 3),
                'total_samples': total,
                'win_count': win_count,
                'loss_count': loss_count,
                'win_mean': round(win_mean, 4),
                'loss_mean': round(loss_mean, 4),
                'discrimination': round(discrimination, 4),
            })
        
        # Sort by discrimination (most discriminative first)
        importance.sort(key=lambda x: x['discrimination'], reverse=True)
        
        return importance
    
    def get_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get summary of outcomes for the last N days."""
        if not self.outcomes_file.exists():
            return {'total': 0, 'wins': 0, 'losses': 0, 'win_rate': 0}
        
        cutoff = datetime.now() - timedelta(days=days)
        total = 0
        wins = 0
        losses = 0
        
        with open(self.outcomes_file, 'r') as f:
            for line in f:
                record = json.loads(line.strip())
                try:
                    record_time = datetime.fromisoformat(record['timestamp'])
                    if record_time < cutoff:
                        continue
                except (KeyError, ValueError):
                    continue
                
                total += 1
                if record.get('outcome') == 'WIN':
                    wins += 1
                elif record.get('outcome') == 'LOSS':
                    losses += 1
        
        return {
            'total': total,
            'wins': wins,
            'losses': losses,
            'win_rate': round(wins / (wins + losses), 3) if (wins + losses) > 0 else 0,
        }
