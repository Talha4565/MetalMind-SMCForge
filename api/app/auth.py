"""
Production-Grade Authentication Module
Implements: JWT, Email OTP, 2FA, Rate Limiting, Session Management
"""

from flask import Blueprint, request, jsonify, make_response
import jwt
import pyotp
import qrcode
import io
import base64
from datetime import datetime, timedelta, timezone
from functools import wraps
import secrets
import re
import os
from flask_limiter.util import get_remote_address

# Import database models and email service
from api.app.database import db, User, Session as DBSession, OTPCode, WatchlistItem
from api.app.services.email_service import email_service
from api.app.extensions import limiter
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

# FIXED: Use centralized security service for SECRET_KEY validation
from api.app.services.security_service import security_service
from api.app.services.password_service import password_service

SECRET_KEY = security_service.validate_secret_key()
_refresh_secret = os.environ.get('REFRESH_SECRET_KEY')
if not _refresh_secret:
    if os.environ.get('FLASK_ENV') == 'production':
        raise RuntimeError("REFRESH_SECRET_KEY environment variable must be set in production")
    _refresh_secret = 'dev-refresh-secret-not-for-production'
REFRESH_SECRET_KEY = _refresh_secret
ACCESS_TOKEN_EXPIRY = timedelta(minutes=15)
REFRESH_TOKEN_EXPIRY = timedelta(days=7)
OTP_EXPIRY = timedelta(minutes=10)

# ==================== HELPER FUNCTIONS ====================

# REMOVED: Duplicate email validation - now using validation_service
from api.app.services.validation_service import validation_service


# REMOVED: Duplicate password validation - now using password_service


# REMOVED: Duplicate OTP generation - now using security_service


def create_access_token(email):
    """Create JWT access token."""
    payload = {
        'email': email,
        'exp': datetime.now(timezone.utc) + ACCESS_TOKEN_EXPIRY,
        'iat': datetime.now(timezone.utc),
        'type': 'access'
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')


def create_refresh_token(email):
    """Create JWT refresh token."""
    payload = {
        'email': email,
        'exp': datetime.now(timezone.utc) + REFRESH_TOKEN_EXPIRY,
        'iat': datetime.now(timezone.utc),
        'type': 'refresh'
    }
    return jwt.encode(payload, REFRESH_SECRET_KEY, algorithm='HS256')


def verify_token(token, token_type='access'):
    """Verify JWT token."""
    try:
        secret = SECRET_KEY if token_type == 'access' else REFRESH_SECRET_KEY
        payload = jwt.decode(token, secret, algorithms=['HS256'])
        if payload.get('type') != token_type:
            return None
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def token_required(f):
    """Decorator to protect routes with JWT authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check for token in Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Invalid token format'}), 401
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Token is invalid or expired'}), 401
        
        # Pass user email to the route
        return f(payload['email'], *args, **kwargs)
    
    return decorated


def send_otp_email(email, otp_code):
    """Send OTP via email using email service."""
    return email_service.send_otp(email, otp_code)


# ==================== AUTH ROUTES ====================

@auth_bp.route('/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    """Register a new user with database storage."""
    try:
        data = request.get_json()
        email = data.get('email', '').lower().strip()
        password = data.get('password', '')
        
        # Validate inputs
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # FIXED: Use centralized validation service
        is_valid, error_msg = validation_service.validate_email(email)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        # FIXED: Use centralized password service
        is_strong, message = password_service.validate_strength(password)
        if not is_strong:
            return jsonify({'error': message}), 400
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'error': 'Email already registered'}), 409
        
        # FIXED: Use centralized password service
        password_hash = password_service.hash_password(password)
        
        # Generate TOTP secret for 2FA
        totp_secret = pyotp.random_base32()
        
        # Create user - auto-verify in development for easier login
        is_dev = os.environ.get('FLASK_ENV') == 'development'
        new_user = User(
            email=email,
            password_hash=password_hash,
            totp_secret=totp_secret,
            is_verified=is_dev  # Auto-verify in dev so login works immediately
        )
        db.session.add(new_user)
        db.session.flush()  # Get user ID
        
        # Generate OTP code
        otp_code = security_service.generate_otp()
        otp = OTPCode(
            user_id=new_user.id,
            code=otp_code,
            expires_at=datetime.now(timezone.utc) + OTP_EXPIRY
        )
        db.session.add(otp)
        db.session.commit()
        
        # Always attempt to send OTP email (even in dev)
        # In dev, email won't actually send but the flow is demonstrated
        otp_sent = False
        try:
            send_otp_email(email, otp_code)
            otp_sent = True
            logger.info(f"OTP email sent to {email}")
        except Exception as e:
            logger.warning(f"Could not send OTP email: {e}")
        
        return jsonify({
            'success': True,
            'message': 'Registration successful. Please verify your email with the OTP sent.',
            'email': email,
            'otp_sent': otp_sent,
            'dev_verified': is_dev,
            'otp_code': otp_code if is_dev else None  # Return OTP in dev for testing
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500


@auth_bp.route('/verify-email', methods=['POST'])
@limiter.limit("10 per minute")
def verify_email():
    """Verify email with OTP code using database."""
    try:
        data = request.get_json()
        email = data.get('email', '').lower().strip()
        otp_code = data.get('otp_code', '').strip()
        
        if not email or not otp_code:
            return jsonify({'error': 'Email and OTP code are required'}), 400
        
        # Find user
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Find valid OTP
        otp = OTPCode.query.filter_by(
            user_id=user.id,
            code=otp_code,
            is_used=False
        ).order_by(OTPCode.created_at.desc()).first()
        
        if not otp:
            return jsonify({'error': 'Invalid OTP code'}), 400
        
        # Check expiry
        if not otp.is_valid():
            return jsonify({'error': 'OTP has expired. Please request a new one.'}), 400
        
        # Mark user as verified
        user.is_verified = True
        otp.is_used = True
        db.session.commit()
        
        # Send welcome email
        email_service.send_welcome_email(email, email.split('@')[0])
        
        return jsonify({
            'success': True,
            'message': 'Email verified successfully. You can now log in.'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Verification failed: {str(e)}'}), 500


@auth_bp.route('/resend-otp', methods=['POST'])
@limiter.limit("3 per minute")
def resend_otp():
    """Resend OTP code using database."""
    try:
        data = request.get_json()
        email = data.get('email', '').lower().strip()
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        # Find user in database
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # FIXED: Use centralized security service
        otp_code = security_service.generate_otp()
        otp = OTPCode(
            user_id=user.id,
            code=otp_code,
            expires_at=datetime.now(timezone.utc) + OTP_EXPIRY
        )
        db.session.add(otp)
        db.session.commit()
        
        # Send OTP email
        send_otp_email(email, otp_code)
        
        return jsonify({
            'success': True,
            'message': 'OTP sent successfully'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to send OTP: {str(e)}'}), 500


@auth_bp.route('/login', methods=['POST'])
@limiter.limit("10 per minute; 50 per hour")
def login():
    """Login with email and password using database."""
    try:
        data = request.get_json()
        email = data.get('email', '').lower().strip()
        password = data.get('password', '')
        totp_code = data.get('totp_code', '')  # Optional 2FA code
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Check if user exists in database
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Check if account is active
        if not user.is_active:
            return jsonify({'error': 'Account is deactivated. Please contact support.'}), 403
        
        # Check if email is verified — no bypass in any environment
        if not user.is_verified:
            return jsonify({'error': 'Email not verified. Please check your email for verification code.'}), 403
        
        # FIXED: Use centralized password service (simplified)
        logger.info(f"Login attempt for: {email}")
        password_valid = password_service.verify_password(password, user.password_hash)
        
        if not password_valid:
            logger.warning(f"Password validation FAILED for {email}")
            return jsonify({'error': 'Invalid email or password'}), 401
        
        logger.info(f"Password validation SUCCESS for {email}")
        
        # Check 2FA if enabled
        if user.totp_enabled:
            if not totp_code:
                return jsonify({
                    'requires_2fa': True,
                    'message': 'Please enter your 2FA code'
                }), 200
            
            totp = pyotp.TOTP(user.totp_secret)
            if not totp.verify(totp_code, valid_window=1):
                return jsonify({'error': 'Invalid 2FA code'}), 401
        
        # Generate tokens
        access_token = create_access_token(email)
        refresh_token = create_refresh_token(email)
        
        # FIXED: Use centralized security service
        session_id = security_service.generate_secure_token(32)
        new_session = DBSession(
            session_id=session_id,
            user_id=user.id,
            ip_address=get_remote_address(),
            user_agent=request.headers.get('User-Agent', '')[:500],
            expires_at=datetime.now(timezone.utc) + REFRESH_TOKEN_EXPIRY
        )
        db.session.add(new_session)
        
        # Update last login
        user.last_login = datetime.now(timezone.utc)
        db.session.commit()
        
        response = make_response(jsonify({
            'success': True,
            'message': 'Login successful',
            'token': access_token,
            'refresh_token': refresh_token,
            'data': {
                'user': {
                    'id': str(user.id),
                    'email': email,
                    'username': email.split('@')[0],
                    'verified': user.is_verified,
                    'createdAt': user.created_at.isoformat() if user.created_at else None,
                    'lastLogin': user.last_login.isoformat() if user.last_login else None
                },
                'tokens': {
                    'accessToken': access_token,
                    'refreshToken': refresh_token
                }
            }
        }), 200)
        
        # Set httpOnly cookies (more secure than localStorage)
        is_production = os.environ.get('FLASK_ENV') == 'production'
        response.set_cookie('refresh_token', refresh_token,
                          httponly=True, secure=is_production, samesite='Lax',
                          max_age=int(REFRESH_TOKEN_EXPIRY.total_seconds()))
        
        return response
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Login failed: {str(e)}'}), 500


@auth_bp.route('/refresh', methods=['POST'])
def refresh_access_token():
    """Refresh an expired access token using a valid refresh token."""
    refresh_token = None
    
    # Try request body first
    data = request.get_json(silent=True) or {}
    refresh_token = data.get('refresh_token')
    
    # Fallback to cookie
    if not refresh_token:
        refresh_token = request.cookies.get('refresh_token')
    
    if not refresh_token:
        return jsonify({'error': 'Refresh token required'}), 400
    
    payload = verify_token(refresh_token, token_type='refresh')
    if not payload:
        return jsonify({'error': 'Invalid or expired refresh token'}), 401
    
    # Issue new access token
    new_access_token = create_access_token(payload['email'])
    
    return jsonify({
        'access_token': new_access_token,
        'token_type': 'Bearer'
    }), 200


# ============================================================================
# FORGOT PASSWORD ENDPOINTS
# ============================================================================

import hashlib

@auth_bp.route('/forgot-password', methods=['POST'])
@limiter.limit("5 per hour")
def forgot_password():
    """
    Send password reset email.

    Security:
    - Hashes token before storing in DB
    - Doesn't reveal if email exists (prevents enumeration)
    - Rate limited to 5/hour per IP
    """
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()

        if not email:
            return jsonify({'error': 'Email is required'}), 400

        # Always return success to prevent email enumeration
        user = User.query.filter_by(email=email).first()

        if user:
            # Generate secure token
            raw_token = secrets.token_urlsafe(32)
            token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

            # Store hashed token with 1-hour expiry
            from api.app.services.password_service import password_service
            user.reset_token = token_hash
            user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
            db.session.commit()

            # Send email with raw token (not hash)
            email_service.send_password_reset(email, raw_token)

            logger.info(f"Password reset requested for {email}")

        # Always return same message (don't reveal email existence)
        return jsonify({'message': 'If email exists, reset link sent'}), 200

    except Exception as e:
        logger.error(f"Forgot password error: {e}")
        return jsonify({'error': 'An error occurred'}), 500


@auth_bp.route('/reset-password', methods=['POST'])
@limiter.limit("10 per hour")
def reset_password():
    """
    Reset password using token.

    Security:
    - Validates token hash against DB
    - Checks token expiry
    - Validates password strength
    - Clears token after successful reset
    """
    try:
        from api.app.services.password_service import password_service

        data = request.get_json()
        token = data.get('token', '').strip()
        new_password = data.get('password', '')

        if not token or not new_password:
            return jsonify({'error': 'Token and password are required'}), 400

        # Validate password strength
        is_strong, message = password_service.validate_strength(new_password)
        if not is_strong:
            return jsonify({'error': message}), 400

        # Hash the incoming token to compare with stored hash
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        # Find user by hashed token
        user = User.query.filter_by(reset_token=token_hash).first()

        if not user:
            return jsonify({'error': 'Invalid or expired token'}), 400

        # Check expiry (timezone-aware comparison)
        if user.reset_token_expires is None:
            return jsonify({'error': 'Invalid token'}), 400

        now = datetime.now(timezone.utc)
        expires = user.reset_token_expires
        # Ensure expiry is timezone-aware for comparison
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)

        if expires < now:
            return jsonify({'error': 'Token expired'}), 400

        # Update password
        user.password_hash = password_service.hash_password(new_password)
        user.reset_token = None
        user.reset_token_expires = None
        db.session.commit()

        logger.info(f"Password reset successful for {user.email}")
        return jsonify({'message': 'Password reset successful'}), 200

    except Exception as e:
        logger.error(f"Reset password error: {e}")
        return jsonify({'error': 'An error occurred'}), 500


# Initialize extensions correctly from shared instances
def init_auth(app):
    """Initialize authentication module with Flask app."""
    # Limiter is already initialized in main.py via init_app
    # Password hashing uses the bcrypt library directly via services/password_service.py
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
