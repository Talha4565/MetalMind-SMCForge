"""
Validation Service - Centralized validation utilities
Single Responsibility: Handle all input validation
"""

import re
from typing import Optional, Tuple, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ValidationService:
    """
    Centralized validation operations.
    Consolidates validators.py functionality into a service class.
    """
    
    # Validation patterns
    EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    # Allowed values
    ALLOWED_ASSETS = {'gold', 'silver', 'latest'}
    ALLOWED_TIMEFRAMES = {'1m', '5m', '15m', '30m', '1h', '4h', '1d'}
    ALLOWED_THEMES = {'dark', 'light'}
    
    # Limits
    MIN_LIMIT = 1
    MAX_LIMIT = 1000
    MAX_EMAIL_LENGTH = 255
    
    @classmethod
    def validate_email(cls, email: str) -> Tuple[bool, Optional[str]]:
        """
        Validate email format.
        
        Args:
            email: Email address to validate
            
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if not email:
            return False, "Email is required"
        
        if not isinstance(email, str):
            return False, "Email must be a string"
        
        if len(email) > cls.MAX_EMAIL_LENGTH:
            return False, f"Email is too long (max {cls.MAX_EMAIL_LENGTH} characters)"
        
        if not re.match(cls.EMAIL_PATTERN, email):
            return False, "Invalid email format"
        
        return True, None
    
    @classmethod
    def validate_asset(cls, asset: str) -> Tuple[bool, Optional[str]]:
        """
        Validate asset symbol.
        
        Args:
            asset: Asset symbol to validate
            
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if not asset:
            return False, "Asset is required"
        
        asset_lower = asset.lower().strip()
        if asset_lower not in cls.ALLOWED_ASSETS:
            return False, f"Invalid asset. Must be one of: {', '.join(cls.ALLOWED_ASSETS)}"
        
        return True, None
    
    @classmethod
    def validate_timeframe(cls, timeframe: str) -> Tuple[bool, Optional[str]]:
        """
        Validate timeframe.
        
        Args:
            timeframe: Timeframe to validate
            
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if not timeframe:
            return False, "Timeframe is required"
        
        if timeframe not in cls.ALLOWED_TIMEFRAMES:
            return False, f"Invalid timeframe. Must be one of: {', '.join(cls.ALLOWED_TIMEFRAMES)}"
        
        return True, None
    
    @classmethod
    def validate_limit(cls, limit: Any) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Validate and parse limit parameter.
        
        Args:
            limit: Limit value to validate
            
        Returns:
            Tuple[bool, Optional[str], Optional[int]]: (is_valid, error_message, parsed_value)
        """
        try:
            limit_int = int(limit)
        except (ValueError, TypeError):
            return False, "Limit must be a valid integer", None
        
        if limit_int < cls.MIN_LIMIT:
            return False, f"Limit must be at least {cls.MIN_LIMIT}", None
        
        if limit_int > cls.MAX_LIMIT:
            return False, f"Limit must not exceed {cls.MAX_LIMIT}", None
        
        return True, None, limit_int
    
    @classmethod
    def validate_theme(cls, theme: str) -> Tuple[bool, Optional[str]]:
        """
        Validate theme value.
        
        Args:
            theme: Theme to validate
            
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if not theme:
            return False, "Theme is required"
        
        if theme not in cls.ALLOWED_THEMES:
            return False, f"Invalid theme. Must be one of: {', '.join(cls.ALLOWED_THEMES)}"
        
        return True, None
    
    @classmethod
    def validate_date_string(cls, date_str: str) -> Tuple[bool, Optional[str], Optional[datetime]]:
        """
        Validate and parse date string.
        
        Args:
            date_str: Date string in ISO format
            
        Returns:
            Tuple[bool, Optional[str], Optional[datetime]]: (is_valid, error_message, parsed_date)
        """
        if not date_str:
            return False, "Date is required", None
        
        try:
            parsed_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return True, None, parsed_date
        except (ValueError, AttributeError) as e:
            return False, f"Invalid date format. Use ISO format (YYYY-MM-DD): {str(e)}", None
    
    @classmethod
    def validate_symbol(cls, symbol: str, allowed_symbols: list) -> Tuple[bool, Optional[str]]:
        """
        Validate symbol against allowed list.
        
        Args:
            symbol: Symbol to validate
            allowed_symbols: List of allowed symbols
            
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if not symbol:
            return False, "Symbol is required"
        
        if symbol not in allowed_symbols:
            return False, f"Invalid symbol. Valid symbols: {', '.join(allowed_symbols)}"
        
        return True, None


# Singleton instance
validation_service = ValidationService()
