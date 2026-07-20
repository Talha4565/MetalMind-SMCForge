"""
Watchlist management API endpoints.
Allows users to add/remove assets to their personal watchlist.
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
from functools import wraps
import logging

from api.app.database import db, WatchlistItem, User
from config.settings import ASSETS
from api.app.extensions import limiter

logger = logging.getLogger(__name__)

# Create blueprint
watchlist_bp = Blueprint('watchlist', __name__, url_prefix='/api/watchlist')


# Import centralized token_required from auth module
from api.app.auth import token_required as auth_token_required

def token_required(f):
    """Wrapper to convert email from auth to User object for watchlist routes."""
    @wraps(f)
    @auth_token_required
    def decorated(email, *args, **kwargs):
        # Convert email to User object
        current_user = User.query.filter_by(email=email).first()
        if not current_user:
            return jsonify({'error': 'User not found'}), 401
        return f(current_user, *args, **kwargs)
    
    return decorated


@watchlist_bp.route('', methods=['GET'])
@token_required
@limiter.limit("60 per minute")
def get_watchlist(current_user):
    """
    Get user's watchlist.
    
    Returns:
        200: List of watchlist items
    """
    items = WatchlistItem.query.filter_by(user_id=current_user.id).order_by(WatchlistItem.order).all()
    
    return jsonify({
        'watchlist': [item.to_dict() for item in items],
        'count': len(items)
    }), 200


@watchlist_bp.route('', methods=['POST'])
@token_required
@limiter.limit("30 per minute")
def add_to_watchlist(current_user):
    """
    Add asset to watchlist.
    
    Body:
        symbol: str - Asset symbol (e.g., 'XAU/USD', 'XAG/USD')
        display_name: str (optional) - Display name (e.g., 'Gold', 'Silver')
        notifications_enabled: bool (optional) - Enable notifications
        alert_threshold: float (optional) - Price alert threshold
        notes: str (optional) - User notes
    
    Returns:
        201: Watchlist item created
        400: Invalid request
        409: Item already exists
    """
    data = request.get_json()
    
    if not data or 'symbol' not in data:
        return jsonify({'error': 'Symbol is required'}), 400
    
    symbol = data['symbol']
    
    # Validate symbol (optional - check against known assets)
    valid_symbols = [asset_config['name'] for asset_config in ASSETS.values()]
    if symbol not in valid_symbols:
        return jsonify({
            'error': f'Invalid symbol. Valid symbols: {", ".join(valid_symbols)}'
        }), 400
    
    # Check if already in watchlist
    existing = WatchlistItem.query.filter_by(
        user_id=current_user.id,
        symbol=symbol
    ).first()
    
    if existing:
        return jsonify({'error': 'Asset already in watchlist'}), 409
    
    # Create watchlist item
    item = WatchlistItem(
        user_id=current_user.id,
        symbol=symbol,
        display_name=data.get('display_name', symbol.split('/')[0]),
        notifications_enabled=data.get('notifications_enabled', True),
        alert_threshold=data.get('alert_threshold'),
        notes=data.get('notes'),
        order=WatchlistItem.query.filter_by(user_id=current_user.id).count()
    )
    
    # FIXED: Add transaction rollback on error
    try:
        db.session.add(item)
        db.session.commit()
        
        return jsonify({
            'message': 'Asset added to watchlist',
            'item': item.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to add watchlist item: {e}")
        return jsonify({'error': 'Failed to add item to watchlist'}), 500


@watchlist_bp.route('/<int:item_id>', methods=['PUT'])
@token_required
def update_watchlist_item(current_user, item_id):
    """
    Update watchlist item.
    
    Body:
        display_name: str (optional)
        notifications_enabled: bool (optional)
        alert_threshold: float (optional)
        notes: str (optional)
        order: int (optional)
    
    Returns:
        200: Item updated
        404: Item not found
    """
    item = WatchlistItem.query.filter_by(
        id=item_id,
        user_id=current_user.id
    ).first()
    
    if not item:
        return jsonify({'error': 'Watchlist item not found'}), 404
    
    data = request.get_json()
    
    # Update fields
    if 'display_name' in data:
        item.display_name = data['display_name']
    if 'notifications_enabled' in data:
        item.notifications_enabled = data['notifications_enabled']
    if 'alert_threshold' in data:
        item.alert_threshold = data['alert_threshold']
    if 'notes' in data:
        item.notes = data['notes']
    if 'order' in data:
        item.order = data['order']
    
    item.updated_at = datetime.now(timezone.utc)
    
    # FIXED: Add transaction rollback on error
    try:
        db.session.commit()
        
        return jsonify({
            'message': 'Watchlist item updated',
            'item': item.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to update watchlist item: {e}")
        return jsonify({'error': 'Failed to update item'}), 500


@watchlist_bp.route('/<int:item_id>', methods=['DELETE'])
@token_required
@limiter.limit("30 per minute")
def remove_from_watchlist(current_user, item_id):
    """
    Remove asset from watchlist.
    
    Returns:
        200: Item removed
        404: Item not found
    """
    item = WatchlistItem.query.filter_by(
        id=item_id,
        user_id=current_user.id
    ).first()
    
    if not item:
        return jsonify({'error': 'Watchlist item not found'}), 404
    
    # FIXED: Add transaction rollback on error
    try:
        db.session.delete(item)
        db.session.commit()
        
        return jsonify({
            'message': 'Asset removed from watchlist'
        }), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to delete watchlist item: {e}")
        return jsonify({'error': 'Failed to remove item'}), 500


@watchlist_bp.route('/reorder', methods=['POST'])
@token_required
def reorder_watchlist(current_user):
    """
    Reorder watchlist items.
    
    Body:
        items: list of {id: int, order: int}
    
    Returns:
        200: Watchlist reordered
        400: Invalid request
    """
    data = request.get_json()
    
    if not data or 'items' not in data:
        return jsonify({'error': 'Items array is required'}), 400
    
    # FIXED: Bulk update to avoid N+1 query problem
    # Extract all item IDs and orders
    updates = {item['id']: item['order'] for item in data['items'] 
               if 'id' in item and 'order' in item}
    
    if not updates:
        return jsonify({'error': 'No valid items provided'}), 400
    
    # Fetch all items in single query
    items = WatchlistItem.query.filter(
        WatchlistItem.id.in_(updates.keys()),
        WatchlistItem.user_id == current_user.id
    ).all()
    
    # Update orders in memory
    for item in items:
        if item.id in updates:
            item.order = updates[item.id]
    
    # FIXED: Add transaction rollback on error
    try:
        db.session.commit()
        return jsonify({'message': 'Watchlist reordered'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to reorder watchlist: {e}")
        return jsonify({'error': 'Failed to reorder watchlist'}), 500


@watchlist_bp.route('/symbols', methods=['GET'])
@limiter.limit("60 per minute")
def get_available_symbols():
    """
    Get list of available symbols that can be added to watchlist.
    
    Returns:
        200: List of available symbols
    """
    symbols = [
        {
            'symbol': config['name'],
            'display_name': asset_name.capitalize(),
            'asset_type': 'metal'
        }
        for asset_name, config in ASSETS.items()
    ]
    
    return jsonify({'symbols': symbols}), 200
