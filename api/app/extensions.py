"""
Flask Extensions - Centralized extension instances
Prevents circular imports and duplication.
"""

import os
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate

# Filesystem-backed rate limit storage — survives server restarts.
# No Redis dependency needed. Counts persist in /tmp/rate_limit/.
_storage = os.environ.get("RATELIMIT_STORAGE_URI", "filesystem:///tmp/rate_limit")

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=_storage,
)

migrate = Migrate()
