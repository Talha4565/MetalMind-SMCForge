"""
User profile management API endpoints.
Allows users to view and update their profile information.
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
from functools import wraps
import logging

from api.app.database import db, User
import bcrypt

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

# Create blueprint
profile_bp = Blueprint('profile', __name__, url_prefix='/api/profile')


# FIXED: Import centralized token_required from auth module
from api.app.auth import token_required as auth_token_required

def token_required(f):
    """Wrapper to convert email from auth to User object for profile routes."""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Use the centralized auth token_required
        def inner(email, *inner_args, **inner_kwargs):
            # Convert email to User object
            current_user = User.query.filter_by(email=email).first()
            if not current_user:
                return jsonify({'error': 'User not found'}), 401
            return f(current_user, *inner_args, **inner_kwargs)
        
        return auth_token_required(inner)(*args, **kwargs)
    
    return decorated


@profile_bp.route('', methods=['GET'])
@token_required
def get_profile(current_user):
    """
    Get user profile information.
    
    Returns:
        200: User profile data
    """
    return jsonify({
        'profile': current_user.to_dict()
    }), 200


@profile_bp.route('', methods=['PUT'])
@token_required
def update_profile(current_user):
    """
    Update user profile information.
    
    Body:
        email: str (optional) - New email address
    
    Returns:
        200: Profile updated
        400: Invalid request
        409: Email already in use
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Update email if provided
    if 'email' in data:
        new_email = data['email'].strip().lower()
        
        # Validate email format
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, new_email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Check if email already exists
        if new_email != current_user.email:
            existing = User.query.filter_by(email=new_email).first()
            if existing:
                return jsonify({'error': 'Email already in use'}), 409
            
            # Update email and mark as unverified
            current_user.email = new_email
            current_user.is_verified = False
            # TODO: Send verification email
    
    current_user.updated_at = datetime.utcnow()
    
    # FIXED: Add transaction rollback on error
    try:
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'profile': current_user.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to update profile: {e}")
        return jsonify({'error': 'Failed to update profile'}), 500


@profile_bp.route('/password', methods=['PUT'])
@token_required
def change_password(current_user):
    """
    Change user password.
    
    Body:
        current_password: str - Current password for verification
        new_password: str - New password
    
    Returns:
        200: Password changed
        400: Invalid request
        401: Incorrect current password
    """
    data = request.get_json()
    
    if not data or 'current_password' not in data or 'new_password' not in data:
        return jsonify({'error': 'Current and new passwords are required'}), 400
    
    current_password = data['current_password']
    new_password = data['new_password']
    
    # Verify current password
    import bcrypt
    if not bcrypt.checkpw(current_password.encode('utf-8'), current_user.password_hash.encode('utf-8')):
        return jsonify({'error': 'Current password is incorrect'}), 401
    
    # Validate new password strength
    if len(new_password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400
    
    if not re.search(r'[A-Z]', new_password):
        return jsonify({'error': 'Password must contain at least one uppercase letter'}), 400
    
    if not re.search(r'[a-z]', new_password):
        return jsonify({'error': 'Password must contain at least one lowercase letter'}), 400
    
    if not re.search(r'[0-9]', new_password):
        return jsonify({'error': 'Password must contain at least one number'}), 400
    
    # Update password
    current_user.password_hash = hash_password(new_password)
    current_user.updated_at = datetime.utcnow()
    
    # FIXED: Add transaction rollback on error
    try:
        db.session.commit()
        
        return jsonify({
            'message': 'Password changed successfully'
        }), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to change password: {e}")
        return jsonify({'error': 'Failed to change password'}), 500


@profile_bp.route('/settings', methods=['GET'])
@token_required
def get_settings(current_user):
    """
    Get user settings/preferences.
    
    Returns:
        200: User settings
    """
    # For now, return basic settings
    # In future, add UserSettings model for more complex preferences
    settings = {
        'theme': 'dark',  # Default theme
        'notifications_enabled': True,
        'email_notifications': True,
        'default_timeframe': '15m',
        'default_asset': 'gold'
    }
    
    return jsonify({'settings': settings}), 200


@profile_bp.route('/settings', methods=['PUT'])
@token_required
def update_settings(current_user):
    """
    Update user settings/preferences.
    
    Body:
        theme: str (optional) - 'dark' or 'light'
        notifications_enabled: bool (optional)
        email_notifications: bool (optional)
        default_timeframe: str (optional)
        default_asset: str (optional)
    
    Returns:
        200: Settings updated
        400: Invalid request
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Validate theme
    if 'theme' in data:
        if data['theme'] not in ['dark', 'light']:
            return jsonify({'error': 'Theme must be "dark" or "light"'}), 400
    
    # Validate default_timeframe
    if 'default_timeframe' in data:
        valid_timeframes = ['5m', '15m', '30m', '1h']
        if data['default_timeframe'] not in valid_timeframes:
            return jsonify({'error': f'Invalid timeframe. Valid options: {", ".join(valid_timeframes)}'}), 400
    
    # Validate default_asset
    if 'default_asset' in data:
        valid_assets = ['gold', 'silver']
        if data['default_asset'] not in valid_assets:
            return jsonify({'error': f'Invalid asset. Valid options: {", ".join(valid_assets)}'}), 400
    
    # TODO: Store settings in database (add UserSettings model)
    # For now, just return success
    
    return jsonify({
        'message': 'Settings updated successfully',
        'settings': data
    }), 200


@profile_bp.route('/delete', methods=['DELETE'])
@token_required
def delete_account(current_user):
    """
    Delete user account (soft delete - mark as inactive).
    
    Body:
        password: str - Password confirmation
    
    Returns:
        200: Account deleted
        401: Incorrect password
    """
    data = request.get_json()
    
    if not data or 'password' not in data:
        return jsonify({'error': 'Password confirmation is required'}), 400
    
    # Verify password
    import bcrypt
    if not bcrypt.checkpw(data['password'].encode('utf-8'), current_user.password_hash.encode('utf-8')):
        return jsonify({'error': 'Incorrect password'}), 401
    
    # Soft delete - mark as inactive
    current_user.is_active = False
    current_user.updated_at = datetime.utcnow()
    
    # FIXED: Add transaction rollback on error
    try:
        db.session.commit()
        
        return jsonify({
            'message': 'Account deleted successfully'
        }), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to delete account: {e}")
        return jsonify({'error': 'Failed to delete account'}), 500
