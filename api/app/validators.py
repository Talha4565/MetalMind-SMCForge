"""
Validation utilities for API requests.
Facade pattern - provides backward compatibility while delegating to centralized services.

NOTE: This module is DEPRECATED. Use services directly:
    - from api.app.services.validation_service import validation_service
    - from api.app.services.password_service import password_service

This file remains for backward compatibility with existing code.
"""

from typing import Optional, Tuple, Any

# Import centralized services
from api.app.services.validation_service import validation_service
from api.app.services.password_service import password_service


class PasswordValidator:
    """
    Validates password strength requirements.
    DEPRECATED: Use password_service directly.
    """
    
    MIN_LENGTH = password_service.MIN_LENGTH
    
    @staticmethod
    def validate(password: str) -> Tuple[bool, Optional[str]]:
        """Validate password strength - delegates to password_service."""
        return password_service.validate_strength(password)
    
    @staticmethod
    def get_requirements() -> dict:
        """Get password requirements as dict."""
        return password_service.get_policy()


class EmailValidator:
    """
    Validates email addresses.
    DEPRECATED: Use validation_service directly.
    """
    
    @staticmethod
    def validate(email: str) -> Tuple[bool, Optional[str]]:
        """Validate email format - delegates to validation_service."""
        return validation_service.validate_email(email)


class AssetValidator:
    """
    Validates asset symbols.
    DEPRECATED: Use validation_service directly.
    """
    
    ALLOWED_ASSETS = validation_service.ALLOWED_ASSETS
    
    @staticmethod
    def validate(asset: str) -> Tuple[bool, Optional[str]]:
        """Validate asset symbol - delegates to validation_service."""
        return validation_service.validate_asset(asset)


class LimitValidator:
    """
    Validates limit parameters.
    DEPRECATED: Use validation_service directly.
    """
    
    MIN_LIMIT = validation_service.MIN_LIMIT
    MAX_LIMIT = validation_service.MAX_LIMIT
    
    @staticmethod
    def validate(limit: Any) -> Tuple[bool, Optional[str], Optional[int]]:
        """Validate and parse limit parameter - delegates to validation_service."""
        return validation_service.validate_limit(limit)


class TimeframeValidator:
    """
    Validates timeframe parameters.
    DEPRECATED: Use validation_service directly.
    """
    
    ALLOWED_TIMEFRAMES = validation_service.ALLOWED_TIMEFRAMES
    
    @staticmethod
    def validate(timeframe: str) -> Tuple[bool, Optional[str]]:
        """Validate timeframe - delegates to validation_service."""
        return validation_service.validate_timeframe(timeframe)
