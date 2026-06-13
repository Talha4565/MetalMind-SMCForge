"""
Database setup with SQLAlchemy
Uses SQLite for demo, easily switchable to PostgreSQL for production
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    """User model with authentication fields."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Verification
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    verification_token = db.Column(db.String(100), nullable=True)
    
    # 2FA
    totp_secret = db.Column(db.String(32), nullable=True)
    totp_enabled = db.Column(db.Boolean, default=False, nullable=False)
    
    # Account status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    sessions = db.relationship('Session', backref='user', lazy=True, cascade='all, delete-orphan')
    watchlist_items = db.relationship('WatchlistItem', backref='user', lazy=True, cascade='all, delete-orphan')
    otp_codes = db.relationship('OTPCode', backref='user', lazy=True, cascade='all, delete-orphan')
    settings = db.relationship('UserSettings', backref='user', lazy=True, uselist=False, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def to_dict(self):
        """Convert user to dictionary (exclude sensitive fields)."""
        return {
            'id': self.id,
            'email': self.email,
            'is_verified': self.is_verified,
            'totp_enabled': self.totp_enabled,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }


class Session(db.Model):
    """Session model for tracking active user sessions."""
    __tablename__ = 'sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Session metadata
    ip_address = db.Column(db.String(45), nullable=True)  # IPv4 or IPv6
    user_agent = db.Column(db.String(500), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_active = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<Session {self.session_id[:8]}... for user {self.user_id}>'
    
    def to_dict(self):
        """Convert session to dictionary."""
        return {
            'session_id': self.session_id,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_active': self.last_active.isoformat() if self.last_active else None
        }


class OTPCode(db.Model):
    """OTP code model for email verification."""
    __tablename__ = 'otp_codes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    code = db.Column(db.String(6), nullable=False)
    
    # Expiry
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False, nullable=False)
    
    def __repr__(self):
        return f'<OTPCode {self.code} for user {self.user_id}>'
    
    def is_valid(self):
        """Check if OTP is still valid."""
        return not self.is_used and datetime.utcnow() < self.expires_at


class WatchlistItem(db.Model):
    """Watchlist item for tracking user's watched symbols."""
    __tablename__ = 'watchlist_items'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Symbol information
    symbol = db.Column(db.String(50), nullable=False)  # e.g., 'XAU/USD'
    display_name = db.Column(db.String(100), nullable=True)  # e.g., 'Gold'
    
    # Settings
    notifications_enabled = db.Column(db.Boolean, default=True, nullable=False)
    alert_threshold = db.Column(db.Float, nullable=True)  # Price alert threshold
    
    # Metadata
    notes = db.Column(db.Text, nullable=True)
    order = db.Column(db.Integer, default=0, nullable=False)  # For drag-drop ordering
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Composite unique constraint
    __table_args__ = (
        db.UniqueConstraint('user_id', 'symbol', name='unique_user_symbol'),
    )
    
    def __repr__(self):
        return f'<WatchlistItem {self.symbol} for user {self.user_id}>'
    
    def to_dict(self):
        """Convert watchlist item to dictionary."""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'display_name': self.display_name,
            'notifications_enabled': self.notifications_enabled,
            'alert_threshold': self.alert_threshold,
            'notes': self.notes,
            'order': self.order,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class UserSettings(db.Model):
    """User preferences/settings persisted in database."""
    __tablename__ = 'user_settings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)

    # UI preferences
    theme = db.Column(db.String(10), default='dark', nullable=False)
    default_timeframe = db.Column(db.String(10), default='15m', nullable=False)
    default_asset = db.Column(db.String(20), default='gold', nullable=False)

    # Notification preferences
    notifications_enabled = db.Column(db.Boolean, default=True, nullable=False)
    email_notifications = db.Column(db.Boolean, default=True, nullable=False)

    # Timestamps
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<UserSettings for user {self.user_id}>'

    def to_dict(self):
        return {
            'theme': self.theme,
            'default_timeframe': self.default_timeframe,
            'default_asset': self.default_asset,
            'notifications_enabled': self.notifications_enabled,
            'email_notifications': self.email_notifications,
        }


class RateLimitLog(db.Model):
    """Rate limiting log for tracking API usage."""
    __tablename__ = 'rate_limit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False, index=True)
    endpoint = db.Column(db.String(255), nullable=False)
    
    # Timestamp
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return f'<RateLimitLog {self.ip_address} - {self.endpoint}>'


def init_database(app):
    """
    Initialize database with Flask app.
    
    Args:
        app: Flask application instance
    """
    # SQLite for demo/development, easily switch to PostgreSQL for production
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config.get(
        'SQLALCHEMY_DATABASE_URI',
        'sqlite:///metalmind_smc.db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # FIXED: Proper connection pooling configuration for production
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,      # Test connections before using
        'pool_recycle': 300,        # Recycle connections every 5 minutes
        'pool_size': 20,            # FIXED: Maximum pool size (default 5 too low)
        'max_overflow': 10,         # FIXED: Allow 10 additional connections
        'pool_timeout': 30,         # FIXED: Timeout after 30 seconds
        'echo_pool': False,         # Don't log pool activity (performance)
    }
    
    db.init_app(app)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✅ Database initialized successfully")
        print(f"📦 Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
