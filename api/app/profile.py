"""
User profile management API endpoints.
Allows users to view and update their profile information.
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import pyotp
import qrcode
import io
import base64
import os
from werkzeug.utils import secure_filename
from functools import wraps
import logging

from api.app.database import db, User, UserSettings
from api.app.services.password_service import password_service
from api.app.services.validation_service import validation_service
from api.app.services.email_service import email_service
from api.app.auth import token_required as auth_token_required
import re

logger = logging.getLogger(__name__)

# Create blueprint
profile_bp = Blueprint('profile', __name__, url_prefix='/api/profile')


# Import centralized token_required from auth module
def token_required(f):
    """Wrapper to convert email from auth to User object for profile routes."""
    @wraps(f)
    @auth_token_required
    def decorated(email, *args, **kwargs):
        # Convert email to User object
        current_user = User.query.filter_by(email=email).first()
        if not current_user:
            return jsonify({'error': 'User not found'}), 401
        return f(current_user, *args, **kwargs)
    
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
            
            # Update email and mark as unverified, then send verification OTP
            current_user.email = new_email
            current_user.is_verified = False
            from api.app.database import OTPCode
            from api.app.services.security_service import security_service
            from datetime import timedelta
            otp_code = security_service.generate_otp()
            otp = OTPCode(
                user_id=current_user.id,
                code=otp_code,
                expires_at=datetime.utcnow() + timedelta(minutes=10)
            )
            db.session.add(otp)
            email_service.send_otp(new_email, otp_code)
    
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
    
    # FIXED: Use centralized password service
    if not password_service.verify_password(current_password, current_user.password_hash):
        return jsonify({'error': 'Current password is incorrect'}), 401
    
    # Validate new password strength
    is_valid, error_msg = password_service.validate_strength(new_password)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    # Update password
    current_user.password_hash = password_service.hash_password(new_password)
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
    # Get or create settings row for this user
    settings = UserSettings.query.filter_by(user_id=current_user.id).first()
    if not settings:
        settings = UserSettings(user_id=current_user.id)
        db.session.add(settings)
        db.session.commit()

    return jsonify({'settings': settings.to_dict()}), 200


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
    
    # Get or create settings row for this user
    settings = UserSettings.query.filter_by(user_id=current_user.id).first()
    if not settings:
        settings = UserSettings(user_id=current_user.id)
        db.session.add(settings)

    # Apply validated updates
    if 'theme' in data:
        settings.theme = data['theme']
    if 'notifications_enabled' in data:
        settings.notifications_enabled = bool(data['notifications_enabled'])
    if 'email_notifications' in data:
        settings.email_notifications = bool(data['email_notifications'])
    if 'default_timeframe' in data:
        settings.default_timeframe = data['default_timeframe']
    if 'default_asset' in data:
        settings.default_asset = data['default_asset']

    try:
        db.session.commit()
        return jsonify({
            'message': 'Settings updated successfully',
            'settings': settings.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to update settings: {e}")
        return jsonify({'error': 'Failed to update settings'}), 500


# ------------------- 2FA Endpoints -------------------


@profile_bp.route('/2fa/setup', methods=['GET'])
@token_required
def get_2fa_setup(current_user):
    """Return provisioning URI and QR code image for TOTP setup."""
    try:
        # Ensure user has a secret
        if not current_user.totp_secret:
            secret = pyotp.random_base32()
            current_user.totp_secret = secret
            db.session.add(current_user)
            db.session.commit()
        else:
            secret = current_user.totp_secret

        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(name=current_user.email, issuer_name='MetalMind SMCForge')

        # Generate QR PNG data URI
        img = qrcode.make(provisioning_uri)
        buf = io.BytesIO()
        # Use positional format argument to support both PIL and PyPNG image backends
        img.save(buf, 'PNG')
        qr_data = base64.b64encode(buf.getvalue()).decode()
        qr_data_uri = f"data:image/png;base64,{qr_data}"

        return jsonify({
            'secret': secret,
            'provisioning_uri': provisioning_uri,
            'qr': qr_data_uri
        }), 200
    except Exception as e:
        logger.error(f"Failed to generate 2FA setup: {e}")
        return jsonify({'error': 'Failed to generate 2FA setup'}), 500


@profile_bp.route('/2fa/enable', methods=['POST'])
@token_required
def enable_2fa(current_user):
    """Enable TOTP 2FA after verifying provided OTP code."""
    data = request.get_json() or {}
    otp_code = str(data.get('otp', '')).strip()
    if not otp_code:
        return jsonify({'error': 'OTP code required'}), 400

    if not current_user.totp_secret:
        return jsonify({'error': 'TOTP not initialized. Get setup first.'}), 400

    totp = pyotp.TOTP(current_user.totp_secret)
    if not totp.verify(otp_code, valid_window=1):
        return jsonify({'error': 'Invalid 2FA code'}), 400

    try:
        current_user.totp_enabled = True
        db.session.commit()
        # Notify user
        email_service.send_2fa_enabled(current_user.email)
        return jsonify({'success': True, 'message': '2FA enabled successfully'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to enable 2FA: {e}")
        return jsonify({'error': 'Failed to enable 2FA'}), 500


@profile_bp.route('/2fa/disable', methods=['POST'])
@token_required
def disable_2fa(current_user):
    """Disable TOTP 2FA after verifying provided OTP code."""
    data = request.get_json() or {}
    otp_code = str(data.get('otp', '')).strip()
    if not otp_code:
        return jsonify({'error': 'OTP code required'}), 400

    if not current_user.totp_secret:
        return jsonify({'error': 'TOTP not initialized'}), 400

    totp = pyotp.TOTP(current_user.totp_secret)
    if not totp.verify(otp_code, valid_window=1):
        return jsonify({'error': 'Invalid 2FA code'}), 400

    try:
        current_user.totp_enabled = False
        db.session.commit()
        return jsonify({'success': True, 'message': '2FA disabled successfully'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to disable 2FA: {e}")
        return jsonify({'error': 'Failed to disable 2FA'}), 500



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
    
    # FIXED: Use centralized password service
    if not password_service.verify_password(data['password'], current_user.password_hash):
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


@profile_bp.route('/avatar', methods=['PUT'])
@token_required
def upload_avatar(current_user):
    """Upload or replace user avatar image. Accepts multipart/form-data with 'avatar' file."""
    if 'avatar' not in request.files:
        return jsonify({'error': 'No file part named avatar provided'}), 400

    file = request.files['avatar']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Validate basic file type via filename and content-type
    allowed_ext = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    filename = secure_filename(file.filename)
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if ext not in allowed_ext:
        return jsonify({'error': f'File type not allowed. Allowed: {", ".join(sorted(allowed_ext))}'}), 400

    # Limit file size (e.g., 2MB)
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    max_size = 2 * 1024 * 1024
    if size > max_size:
        return jsonify({'error': 'File too large (limit 2MB)'}), 400

    try:
        avatars_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'avatars')
        os.makedirs(avatars_dir, exist_ok=True)
        dest_filename = f'user_{current_user.id}.{ext}'
        dest_path = os.path.join(avatars_dir, dest_filename)
        file.save(dest_path)

        # Save public path in user settings
        settings = current_user.settings
        if not settings:
            from api.app.database import UserSettings
            settings = UserSettings(user_id=current_user.id)
            db.session.add(settings)

        settings.avatar_url = f'/static/avatars/{dest_filename}'
        db.session.commit()

        return jsonify({'message': 'Avatar uploaded', 'profile': current_user.to_dict(), 'avatar_url': settings.avatar_url}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to upload avatar: {e}")
        return jsonify({'error': 'Failed to upload avatar'}), 500
