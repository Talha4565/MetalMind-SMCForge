"""
Flask Extensions - Centralized extension instances
Prevents circular imports and duplication.
"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate

# Rate limit storage — memory:// is the only zero-dependency option.
# For production with persistent limits across restarts, set
# RATELIMIT_STORAGE_URI=redis://host:port in your environment
# and add redis to requirements.txt.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

migrate = Migrate()
