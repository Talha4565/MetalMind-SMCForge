"""Alert API endpoints."""
from flask import Blueprint, jsonify, request
from api.app.price_alerts import get_active_alerts, get_alert_history, clear_old_alerts
from api.app.auth import token_required
import logging

logger = logging.getLogger(__name__)
alert_bp = Blueprint('alerts', __name__, url_prefix='/api/alerts')


@alert_bp.route('/active', methods=['GET'])
@token_required
def list_active(current_user_email):
    """Get all active price alerts."""
    alerts = get_active_alerts()
    return jsonify({'alerts': alerts, 'count': len(alerts)})


@alert_bp.route('/history', methods=['GET'])
@token_required
def list_history(current_user_email):
    """Get recent triggered alerts."""
    limit = int(request.args.get('limit', 50))
    alerts = get_alert_history(limit=limit)
    return jsonify({'alerts': alerts, 'count': len(alerts)})


@alert_bp.route('/clear', methods=['POST'])
@token_required
def clear_old(current_user_email):
    """Clear alerts older than N days."""
    days = int(request.args.get('days', 7))
    clear_old_alerts(days=days)
    return jsonify({'message': f'Cleared alerts older than {days} days'})
