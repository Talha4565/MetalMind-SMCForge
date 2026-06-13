"""
Security Service - Centralized security utilities
Single Responsibility: Handle all security-related operations
"""

import os
import secrets
import hashlib
from pathlib import Path
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class SecurityService:
    """Centralized security operations following Single Responsibility Principle."""
    
    @staticmethod
    def validate_secret_key() -> str:
        """
        Validate and get SECRET_KEY from environment.
        Exits in production if not set properly.
        
        Returns:
            str: Valid SECRET_KEY
        """
        secret_key = os.environ.get('FLASK_SECRET_KEY') or os.environ.get('SECRET_KEY')
        
        # Check if key is set and not default
        if not secret_key or secret_key == 'your-secret-key-change-in-production-2024':
            if os.environ.get('FLASK_ENV') == 'production':
                logger.critical("❌ CRITICAL: SECRET_KEY must be set in production!")
                logger.critical("   Set environment variable: export SECRET_KEY='your-strong-random-key'")
                raise ValueError("SECRET_KEY not configured for production")
            else:
                logger.warning("⚠️  Using default SECRET_KEY - DO NOT USE IN PRODUCTION!")
                return 'dev-secret-key-only-for-development-123'
        
        return secret_key
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """
        Generate cryptographically secure token.
        
        Args:
            length: Token length in bytes
            
        Returns:
            str: URL-safe token
        """
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def generate_otp(digits: int = 6) -> str:
        """
        Generate numeric OTP code.
        
        Args:
            digits: Number of digits (default 6)
            
        Returns:
            str: Zero-padded OTP code
        """
        max_value = 10 ** digits
        return str(secrets.randbelow(max_value)).zfill(digits)
    
    @staticmethod
    def validate_file_path(base_dir: Path, requested_path: str) -> Tuple[bool, Optional[Path]]:
        """
        Validate file path to prevent directory traversal attacks.
        
        Args:
            base_dir: Base directory to restrict access to
            requested_path: User-requested file path
            
        Returns:
            Tuple[bool, Optional[Path]]: (is_valid, resolved_path)
        """
        try:
            # Resolve the full path
            base = base_dir.resolve()
            requested = (base / requested_path).resolve()
            
            # Check if requested path is within base directory
            if not str(requested).startswith(str(base)):
                logger.warning(f"Path traversal attempt blocked: {requested_path}")
                return False, None
            
            # Check if file exists
            if not requested.exists():
                return False, None
            
            return True, requested
            
        except Exception as e:
            logger.error(f"File path validation error: {e}")
            return False, None
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to prevent security issues.
        
        Args:
            filename: Original filename
            
        Returns:
            str: Sanitized filename
        """
        # Remove path separators and null bytes
        sanitized = filename.replace('/', '').replace('\\', '').replace('\0', '')
        
        # Remove leading dots (hidden files)
        sanitized = sanitized.lstrip('.')
        
        # Limit length
        max_length = 255
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized
    
    @staticmethod
    def hash_file(file_path: Path) -> str:
        """
        Generate SHA256 hash of file for integrity verification.
        
        Args:
            file_path: Path to file
            
        Returns:
            str: Hex digest of file hash
        """
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        return sha256_hash.hexdigest()


# Singleton instance
security_service = SecurityService()
