"""
Long-polling helper for Flask.

Usage in a route:
    from api.app.long_poll import long_poll

    @app.route('/api/health')
    def health():
        return long_poll(
            etag_key='health',
            check_fn=lambda: compute_health(),  # returns (etag, data)
            timeout=30,
        )

The client sends `If-None-Match: <etag>`.
If data unchanged, the server holds the connection up to `timeout` seconds,
checking `check_fn` every `interval` seconds.
Returns 304 if nothing changed, or 200 with new data.
"""

import hashlib
import json
import time
import threading
from datetime import datetime, timezone
from flask import request, Response

_lock = threading.Lock()
_states: dict[str, dict] = {}  # etag_key -> {etag, last_changed}


def make_etag(data) -> str:
    stable = {k: v for k, v in data.items() if k != 'timestamp'}
    # Also exclude nested volatile fields (connection_pool counters, circuit_breaker state)
    if isinstance(stable.get('checks'), dict):
        checks = dict(stable['checks'])
        checks.pop('connection_pool', None)
        checks.pop('circuit_breaker', None)
        stable['checks'] = checks
    raw = json.dumps(stable, sort_keys=True, default=str)
    return hashlib.md5(raw.encode()).hexdigest()


def register_change(etag_key: str):
    """Signal that data for etag_key has changed. Call this after mutations."""
    with _lock:
        _states[etag_key] = {
            'etag': None,
            'last_changed': time.time(),
        }


def long_poll(etag_key: str, check_fn, timeout: int = 30, interval: float = 1.0):
    """
    Long-poll endpoint.

    Args:
        etag_key: unique identifier for this data source
        check_fn: callable that returns (etag_str, response_data).
                  Called once immediately, then repeatedly during hold.
        timeout: max seconds to hold the connection (default 30)
        interval: seconds between re-checks during hold (default 1)

    Returns:
        Flask Response — either 200 with JSON body, or 304 Not Modified.
    """
    client_etag = request.headers.get('If-None-Match')

    # First check — immediate
    etag, data = check_fn()

    # If client has current data and nothing changed since, start holding
    if client_etag and client_etag == etag:
        deadline = time.time() + timeout
        while time.time() < deadline:
            time.sleep(interval)
            new_etag, new_data = check_fn()
            if new_etag != etag:
                etag, data = new_etag, new_data
                break
        else:
            # Timeout — nothing changed
            return Response(status=304, headers={'ETag': etag})

    # Return fresh data
    resp = Response(
        json.dumps(data, default=str),
        status=200,
        mimetype='application/json',
        headers={'ETag': etag, 'Cache-Control': 'no-cache'},
    )
    return resp
