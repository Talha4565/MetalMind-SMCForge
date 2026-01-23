"""
Production-Grade Authentication Module
Implements: JWT, Email OTP, 2FA, Rate Limiting, Session Management
"""

from flask import Blueprint, request, jsonify, make_response
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import jwt
import pyotp
import qrcode
import io
import base64
from datetime import datetime, timedelta
from functools import wraps
import secrets
import re
import os

# Import database models and email service
from api.app.database import db, User, Session as DBSession, OTPCode, WatchlistItem
from api.app.services.email_service import email_service

auth_bp = Blueprint('auth', __name__)
bcrypt = Bcrypt()

# Configuration (use environment variables in production)
# FIXED: Validate SECRET_KEY properly
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY or SECRET_KEY == 'your-secret-key-change-in-production-2024':
    import sys
    if os.environ.get('FLASK_ENV') == 'production':
        print("❌ CRITICAL: SECRET_KEY must be set in production!")
        print("   Set environment variable: export SECRET_KEY='your-strong-random-key'")
        sys.exit(1)
    else:
        import logging
        logging.warning("⚠️  Using default SECRET_KEY - DO NOT USE IN PRODUCTION!")
        SECRET_KEY = 'dev-secret-key-only-for-development-123'
REFRESH_SECRET_KEY = os.environ.get('REFRESH_SECRET_KEY', 'your-refresh-secret-key-2024')
ACCESS_TOKEN_EXPIRY = timedelta(minutes=15)
REFRESH_TOKEN_EXPIRY = timedelta(days=7)
OTP_EXPIRY = timedelta(minutes=10)

# Initialize rate limiter with storage backend
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"  # Explicitly set in-memory storage for demo
)


# ==================== HELPER FUNCTIONS ====================

def validate_email(email):
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password_strength(password):
    """Validate password strength."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    return True, "Password is strong"


def generate_otp():
    """Generate 6-digit OTP."""
    return str(secrets.randbelow(1000000)).zfill(6)


def create_access_token(email):
    """Create JWT access token."""
    payload = {
        'email': email,
        'exp': datetime.utcnow() + ACCESS_TOKEN_EXPIRY,
        'iat': datetime.utcnow(),
        'type': 'access'
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')


def create_refresh_token(email):
    """Create JWT refresh token."""
    payload = {
        'email': email,
        'exp': datetime.utcnow() + REFRESH_TOKEN_EXPIRY,
        'iat': datetime.utcnow(),
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
        
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Check password strength
        is_strong, message = validate_password_strength(password)
        if not is_strong:
            return jsonify({'error': message}), 400
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'error': 'Email already registered'}), 409
        
        # Hash password
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        
        # Generate TOTP secret for 2FA
        totp_secret = pyotp.random_base32()
        
        # Create user (unverified)
        new_user = User(
            email=email,
            password_hash=password_hash,
            totp_secret=totp_secret,
            is_verified=False
        )
        db.session.add(new_user)
        db.session.flush()  # Get user ID
        
        # Generate and send OTP for email verification
        otp_code = generate_otp()
        otp = OTPCode(
            user_id=new_user.id,
            code=otp_code,
            expires_at=datetime.utcnow() + OTP_EXPIRY
        )
        db.session.add(otp)
        db.session.commit()
        
        # Send OTP email
        send_otp_email(email, otp_code)
        
        return jsonify({
            'success': True,
            'message': 'Registration successful. Please verify your email with the OTP sent.',
            'email': email,
            'otp_sent': True
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
        
        # Generate new OTP
        otp_code = generate_otp()
        otp = OTPCode(
            user_id=user.id,
            code=otp_code,
            expires_at=datetime.utcnow() + OTP_EXPIRY
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
        
        # FIXED: Remove auto-verification bypass for production
        # Check if email is verified
        if not user.is_verified:
            # Only auto-verify in development mode
            if os.environ.get('FLASK_ENV') != 'production':
                user.is_verified = True
                db.session.commit()
            else:
                return jsonify({'error': 'Email not verified. Please check your email for verification code.'}), 403
        
        # Verify password using bcrypt directly (not Flask-Bcrypt wrapper)
        import bcrypt as raw_bcrypt
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"Login attempt for: {email}")
        logger.info(f"Password hash: {user.password_hash[:20]}...")
        
        try:
            password_valid = raw_bcrypt.checkpw(
                password.encode('utf-8'),
                user.password_hash.encode('utf-8')
            )
            logger.info(f"raw_bcrypt result: {password_valid}")
        except Exception as e:
            logger.error(f"raw_bcrypt error: {e}")
            # Fallback to Flask-Bcrypt if raw bcrypt fails
            password_valid = bcrypt.check_password_hash(user.password_hash, password)
            logger.info(f"Flask-Bcrypt result: {password_valid}")
        
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
        
        # Create session in database
        session_id = secrets.token_urlsafe(32)
        new_session = DBSession(
            session_id=session_id,
            user_id=user.id,
            ip_address=get_remote_address(),
            user_agent=request.headers.get('User-Agent', '')[:500],
            expires_at=datetime.utcnow() + REFRESH_TOKEN_EXPIRY
        )
        db.session.add(new_session)
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        response = make_response(jsonify({
            'success': True,
            'message': 'Login successful',
            'token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'email': email,
                'totp_enabled': user.totp_enabled
            }
        }), 200)
        
        # Set httpOnly cookies (more secure than localStorage)
        response.set_cookie('refresh_token', refresh_token, 
                          httponly=True, secure=False, samesite='Lax',
                          max_age=int(REFRESH_TOKEN_EXPIRY.total_seconds()))
        
        return response
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Login failed: {str(e)}'}), 500


# Initialize bcrypt with app (call this from main.py)
def init_auth(app):
    """Initialize authentication module with Flask app."""
    bcrypt.init_app(app)
    limiter.init_app(app)
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
