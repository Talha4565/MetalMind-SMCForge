"""
Password Service - Centralized password operations
Single Responsibility: Handle all password-related operations
"""

import bcrypt
import re
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class PasswordService:
    """
    Centralized password operations following Single Responsibility Principle.
    Eliminates code duplication across auth.py and profile.py.
    """
    
    # Password policy configuration
    MIN_LENGTH = 8
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGIT = True
    REQUIRE_SPECIAL = True
    
    # Bcrypt rounds (higher = more secure but slower)
    BCRYPT_ROUNDS = 12
    
    @classmethod
    def hash_password(cls, password: str) -> str:
        """
        Hash password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            str: Bcrypt hashed password
        """
        salt = bcrypt.gensalt(rounds=cls.BCRYPT_ROUNDS)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @classmethod
    def verify_password(cls, password: str, password_hash: str) -> bool:
        """
        Verify password against hash.
        
        Args:
            password: Plain text password to verify
            password_hash: Stored bcrypt hash
            
        Returns:
            bool: True if password matches hash
        """
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                password_hash.encode('utf-8')
            )
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    @classmethod
    def validate_strength(cls, password: str) -> Tuple[bool, Optional[str]]:
        """
        Validate password strength according to policy.
        
        Args:
            password: Password to validate
            
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if len(password) < cls.MIN_LENGTH:
            return False, f"Password must be at least {cls.MIN_LENGTH} characters long"
        
        if cls.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if cls.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if cls.REQUIRE_DIGIT and not re.search(r'\d', password):
            return False, "Password must contain at least one number"
        
        if cls.REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
        
        return True, None
    
    @classmethod
    def get_policy(cls) -> dict:
        """
        Get password policy as dictionary.
        
        Returns:
            dict: Password policy requirements
        """
        return {
            'min_length': cls.MIN_LENGTH,
            'requires_uppercase': cls.REQUIRE_UPPERCASE,
            'requires_lowercase': cls.REQUIRE_LOWERCASE,
            'requires_digit': cls.REQUIRE_DIGIT,
            'requires_special': cls.REQUIRE_SPECIAL
        }


# Singleton instance
password_service = PasswordService()
