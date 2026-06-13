"""
Error Handler Middleware - Centralized error handling
Single Responsibility: Handle all API errors consistently
"""

from flask import jsonify
from werkzeug.exceptions import HTTPException
import logging

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base API error class."""
    
    def __init__(self, message: str, status_code: int = 400, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload
    
    def to_dict(self):
        """Convert error to dictionary."""
        rv = dict(self.payload or ())
        rv['error'] = self.message
        rv['status_code'] = self.status_code
        return rv


class ValidationError(APIError):
    """Validation error (400)."""
    def __init__(self, message: str, payload=None):
        super().__init__(message, status_code=400, payload=payload)


class AuthenticationError(APIError):
    """Authentication error (401)."""
    def __init__(self, message: str = "Authentication required", payload=None):
        super().__init__(message, status_code=401, payload=payload)


class AuthorizationError(APIError):
    """Authorization error (403)."""
    def __init__(self, message: str = "Access forbidden", payload=None):
        super().__init__(message, status_code=403, payload=payload)


class NotFoundError(APIError):
    """Not found error (404)."""
    def __init__(self, message: str = "Resource not found", payload=None):
        super().__init__(message, status_code=404, payload=payload)


class ConflictError(APIError):
    """Conflict error (409)."""
    def __init__(self, message: str, payload=None):
        super().__init__(message, status_code=409, payload=payload)


class RateLimitError(APIError):
    """Rate limit error (429)."""
    def __init__(self, message: str = "Too many requests", payload=None):
        super().__init__(message, status_code=429, payload=payload)


class ServerError(APIError):
    """Server error (500)."""
    def __init__(self, message: str = "Internal server error", payload=None):
        super().__init__(message, status_code=500, payload=payload)


def register_error_handlers(app):
    """
    Register error handlers with Flask app.
    
    Args:
        app: Flask application instance
    """
    
    @app.errorhandler(APIError)
    def handle_api_error(error):
        """Handle custom API errors."""
        logger.warning(f"API Error: {error.message} (Status: {error.status_code})")
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Handle Werkzeug HTTP exceptions."""
        logger.warning(f"HTTP Exception: {error.description} (Status: {error.code})")
        response = jsonify({
            'error': error.description,
            'status_code': error.code
        })
        response.status_code = error.code
        return response
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Handle unexpected errors."""
        logger.error(f"Unexpected error: {str(error)}", exc_info=True)
        response = jsonify({
            'error': 'An unexpected error occurred',
            'status_code': 500
        })
        response.status_code = 500
        return response
    
    @app.errorhandler(404)
    def handle_404(error):
        """Handle 404 errors."""
        return jsonify({
            'error': 'Endpoint not found',
            'status_code': 404
        }), 404
    
    @app.errorhandler(405)
    def handle_405(error):
        """Handle method not allowed errors."""
        return jsonify({
            'error': 'Method not allowed',
            'status_code': 405
        }), 405
