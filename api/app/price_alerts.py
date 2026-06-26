"""Price alert system — monitors live price against active TP/SL levels."""
import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

ALERTS_FILE = Path(__file__).parent.parent.parent / 'reports' / 'active_alerts.json'
ALERTS_LOG = Path(__file__).parent.parent.parent / 'reports' / 'alert_history.jsonl'


def load_alerts():
    if ALERTS_FILE.exists():
        return json.loads(ALERTS_FILE.read_text())
    return []


def save_alerts(alerts):
    ALERTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    ALERTS_FILE.write_text(json.dumps(alerts, indent=2, default=str))


def add_alert(asset, signal, entry_price, tp_level, sl_level, confidence):
    """Register a new trade alert."""
    alerts = load_alerts()
    alert = {
        'id': f"{asset}_{int(datetime.now(timezone.utc).timestamp())}",
        'asset': asset,
        'signal': 'BUY' if signal == 1 else 'SELL',
        'entry': round(entry_price, 2),
        'tp': round(tp_level, 2),
        'sl': round(sl_level, 2),
        'confidence': round(confidence * 100, 1),
        'created_at': datetime.now(timezone.utc).isoformat(),
        'status': 'active',
        'hit_at': None,
        'result': None,
    }
    alerts.append(alert)
    save_alerts(alerts)
    logger.info(f"Alert created: {alert['signal']} {asset} entry={entry_price} TP={tp_level} SL={sl_level}")
    return alert


def check_alerts(current_prices):
    """Check all active alerts against current prices. Returns list of triggered alerts."""
    alerts = load_alerts()
    triggered = []
    changed = False

    for alert in alerts:
        if alert['status'] != 'active':
            continue

        price = current_prices.get(alert['asset'])
        if price is None:
            continue

        entry = alert['entry']
        tp = alert['tp']
        sl = alert['sl']
        signal = alert['signal']

        hit = None
        if signal == 'BUY':
            if price >= tp:
                hit = 'WIN_TP'
            elif price <= sl:
                hit = 'LOSS_SL'
        else:
            if price <= tp:
                hit = 'WIN_TP'
            elif price >= sl:
                hit = 'LOSS_SL'

        if hit:
            alert['status'] = 'triggered'
            alert['hit_at'] = datetime.now(timezone.utc).isoformat()
            alert['result'] = hit
            alert['exit_price'] = round(price, 2)
            pnl_pct = ((price - entry) / entry * 100) if signal == 'BUY' else ((entry - price) / entry * 100)
            alert['pnl_pct'] = round(pnl_pct, 2)
            triggered.append(alert)
            changed = True

            # Log to history
            ALERTS_LOG.parent.mkdir(parents=True, exist_ok=True)
            with open(ALERTS_LOG, 'a') as f:
                f.write(json.dumps(alert, default=str) + '\n')

            logger.info(f"ALERT TRIGGERED: {hit} {alert['asset']} {signal} @ {price:.2f} (PnL: {pnl_pct:+.2f}%)")

    if changed:
        save_alerts(alerts)

    return triggered


def get_active_alerts():
    """Get all currently active alerts."""
    return [a for a in load_alerts() if a['status'] == 'active']


def get_alert_history(limit=50):
    """Get recent triggered alerts."""
    if not ALERTS_LOG.exists():
        return []
    alerts = []
    with open(ALERTS_LOG, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                alerts.append(json.loads(line))
    return alerts[-limit:]


def clear_old_alerts(days=7):
    """Remove alerts older than N days."""
    alerts = load_alerts()
    cutoff = datetime.now(timezone.utc).timestamp() - (days * 86400)
    filtered = []
    for a in alerts:
        try:
            created = datetime.fromisoformat(a['created_at']).timestamp()
            if created > cutoff or a['status'] == 'active':
                filtered.append(a)
        except Exception:
            filtered.append(a)
    save_alerts(filtered)
