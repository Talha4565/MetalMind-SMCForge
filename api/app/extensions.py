"""
Flask Extensions - Centralized extension instances
Prevents circular imports and duplication.
"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate

# Initialize extensions without app
# They will be initialized with app later using init_app()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

migrate = Migrate()
