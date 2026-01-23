"""
Validation utilities for API requests.
Centralized validation logic for consistency.
"""

import re
from typing import Optional, Tuple


class PasswordValidator:
    """Validates password strength requirements."""
    
    MIN_LENGTH = 8
    
    @staticmethod
    def validate(password: str) -> Tuple[bool, Optional[str]]:
        """
        Validate password strength.
        
        Args:
            password: Password to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(password) < PasswordValidator.MIN_LENGTH:
            return False, f"Password must be at least {PasswordValidator.MIN_LENGTH} characters long"
        
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r'\d', password):
            return False, "Password must contain at least one number"
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
        
        return True, None
    
    @staticmethod
    def get_requirements() -> dict:
        """Get password requirements as dict."""
        return {
            'min_length': PasswordValidator.MIN_LENGTH,
            'requires_uppercase': True,
            'requires_lowercase': True,
            'requires_number': True,
            'requires_special': True
        }


class EmailValidator:
    """Validates email addresses."""
    
    EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    @staticmethod
    def validate(email: str) -> Tuple[bool, Optional[str]]:
        """
        Validate email format.
        
        Args:
            email: Email to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not email:
            return False, "Email is required"
        
        if not re.match(EmailValidator.EMAIL_REGEX, email):
            return False, "Invalid email format"
        
        if len(email) > 255:
            return False, "Email is too long (max 255 characters)"
        
        return True, None


class AssetValidator:
    """Validates asset symbols."""
    
    ALLOWED_ASSETS = {'gold', 'silver', 'latest'}
    
    @staticmethod
    def validate(asset: str) -> Tuple[bool, Optional[str]]:
        """
        Validate asset symbol.
        
        Args:
            asset: Asset symbol to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not asset:
            return False, "Asset is required"
        
        asset_lower = asset.lower()
        if asset_lower not in AssetValidator.ALLOWED_ASSETS:
            return False, f"Invalid asset. Must be one of: {', '.join(AssetValidator.ALLOWED_ASSETS)}"
        
        return True, None


class LimitValidator:
    """Validates limit parameters."""
    
    MIN_LIMIT = 1
    MAX_LIMIT = 1000
    
    @staticmethod
    def validate(limit: any) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Validate and parse limit parameter.
        
        Args:
            limit: Limit value to validate (can be string or int)
            
        Returns:
            Tuple of (is_valid, error_message, parsed_value)
        """
        try:
            limit_int = int(limit)
        except (ValueError, TypeError):
            return False, "Limit must be a valid integer", None
        
        if limit_int < LimitValidator.MIN_LIMIT:
            return False, f"Limit must be at least {LimitValidator.MIN_LIMIT}", None
        
        if limit_int > LimitValidator.MAX_LIMIT:
            return False, f"Limit must not exceed {LimitValidator.MAX_LIMIT}", None
        
        return True, None, limit_int


class TimeframeValidator:
    """Validates timeframe parameters."""
    
    ALLOWED_TIMEFRAMES = {'1m', '5m', '15m', '30m', '1h', '4h', '1d'}
    
    @staticmethod
    def validate(timeframe: str) -> Tuple[bool, Optional[str]]:
        """
        Validate timeframe.
        
        Args:
            timeframe: Timeframe to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not timeframe:
            return False, "Timeframe is required"
        
        if timeframe not in TimeframeValidator.ALLOWED_TIMEFRAMES:
            return False, f"Invalid timeframe. Must be one of: {', '.join(TimeframeValidator.ALLOWED_TIMEFRAMES)}"
        
        return True, None
