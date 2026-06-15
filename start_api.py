"""
Simple startup script for ML Signals Flask API
Bypasses the hanging import issue in main.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

print('🚀 Starting ML Signals API server...')

from api.app.main import app, socketio

print('✅ Imported Flask app and SocketIO from api.app.main')


print('✅ Initialization OK')
print('🚀 Server starting on http://0.0.0.0:5000')

# Run server
socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)