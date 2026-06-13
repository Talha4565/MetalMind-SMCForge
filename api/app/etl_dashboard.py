"""ETL Monitoring Dashboard - Simple HTML page for exam committee demo."""

from flask import Blueprint, render_template_string, jsonify, request
from flask_jwt_extended import jwt_required
from api.app.auth import token_required
import logging

dashboard_bp = Blueprint('etl_dashboard', __name__, url_prefix='/etl')
logger = logging.getLogger(__name__)

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ETL Pipeline Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            margin-bottom: 30px;
            text-align: center;
        }
        h1 { color: #333; margin-bottom: 10px; }
        .subtitle { color: #666; font-size: 14px; }
        .cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .card-title { font-size: 18px; font-weight: 600; color: #333; }
        .status-badge {
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }
        .status-success { background: #10b981; color: white; }
        .status-running { background: #3b82f6; color: white; }
        .status-failed { background: #ef4444; color: white; }
        .status-pending { background: #f59e0b; color: white; }
        .metric { margin: 10px 0; display: flex; justify-content: space-between; }
        .metric-label { color: #666; font-size: 14px; }
        .metric-value { color: #333; font-weight: 600; font-size: 16px; }
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            font-size: 14px;
            margin: 5px;
            transition: all 0.3s;
        }
        .btn-primary { background: #3b82f6; color: white; }
        .btn-primary:hover { background: #2563eb; transform: translateY(-2px); }
        .btn-success { background: #10b981; color: white; }
        .btn-success:hover { background: #059669; }
        .btn-danger { background: #ef4444; color: white; }
        .btn-danger:hover { background: #dc2626; }
        .controls {
            background: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            text-align: center;
        }
        .log {
            background: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            margin-top: 20px;
            max-height: 300px;
            overflow-y: auto;
        }
        .log-entry {
            padding: 8px;
            margin: 5px 0;
            border-left: 3px solid #3b82f6;
            background: #f3f4f6;
            font-size: 13px;
            font-family: monospace;
        }
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #3b82f6;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔄 ETL Pipeline Dashboard</h1>
            <p class="subtitle">ML Trading Signals - Data Processing Monitor</p>
        </div>

        <div class="cards" id="pipeline-cards">
            <div class="card">
                <div class="card-header">
                    <span class="card-title">Gold Pipeline</span>
                    <span class="status-badge status-pending" id="gold-status">Pending</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Last Run:</span>
                    <span class="metric-value" id="gold-lastrun">Never</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Records:</span>
                    <span class="metric-value" id="gold-records">0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Features:</span>
                    <span class="metric-value" id="gold-features">0</span>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <span class="card-title">Silver Pipeline</span>
                    <span class="status-badge status-pending" id="silver-status">Pending</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Last Run:</span>
                    <span class="metric-value" id="silver-lastrun">Never</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Records:</span>
                    <span class="metric-value" id="silver-records">0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Features:</span>
                    <span class="metric-value" id="silver-features">0</span>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <span class="card-title">Scheduler</span>
                    <span class="status-badge status-pending" id="scheduler-status">Stopped</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Active Jobs:</span>
                    <span class="metric-value" id="scheduler-jobs">0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Interval:</span>
                    <span class="metric-value">15 minutes</span>
                </div>
            </div>
        </div>

        <div class="controls">
            <h3 style="margin-bottom: 15px;">Pipeline Controls</h3>
            <button class="btn btn-primary" onclick="runPipeline('gold')">▶️ Run Gold</button>
            <button class="btn btn-primary" onclick="runPipeline('silver')">▶️ Run Silver</button>
            <button class="btn btn-success" onclick="startScheduler()">🕒 Start Scheduler</button>
            <button class="btn btn-danger" onclick="stopScheduler()">⏹️ Stop Scheduler</button>
            <button class="btn btn-primary" onclick="refreshData()">🔄 Refresh</button>
        </div>

        <div class="log">
            <h3 style="margin-bottom: 10px;">Activity Log</h3>
            <div id="log-container">
                <div class="log-entry">System initialized. Ready for ETL operations.</div>
            </div>
        </div>
    </div>

    <script>
        function addLog(message) {
            const logContainer = document.getElementById('log-container');
            const entry = document.createElement('div');
            entry.className = 'log-entry';
            entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
            logContainer.insertBefore(entry, logContainer.firstChild);
        }

        // Get auth token from Authorization header passed via query param on dashboard load
        const authToken = new URLSearchParams(window.location.search).get('token') || '';
        const authHeaders = {
            'Content-Type': 'application/json',
            'Authorization': authToken ? `Bearer ${authToken}` : ''
        };

        async function runPipeline(asset) {
            addLog(`Starting ${asset.toUpperCase()} pipeline...`);
            try {
                const response = await fetch('/api/etl/run', {
                    method: 'POST',
                    headers: authHeaders,
                    body: JSON.stringify({ asset, async: true })
                });
                const data = await response.json();
                addLog(`${asset.toUpperCase()} pipeline: ${data.message}`);
                setTimeout(refreshData, 2000);
            } catch (error) {
                addLog(`Error: ${error.message}`);
            }
        }

        async function startScheduler() {
            addLog('Starting scheduler...');
            try {
                const response = await fetch('/api/etl/schedule/start', { method: 'POST', headers: authHeaders });
                const data = await response.json();
                addLog(data.message);
                refreshData();
            } catch (error) {
                addLog(`Error: ${error.message}`);
            }
        }

        async function stopScheduler() {
            addLog('Stopping scheduler...');
            try {
                const response = await fetch('/api/etl/schedule/stop', { method: 'POST', headers: authHeaders });
                const data = await response.json();
                addLog(data.message);
                refreshData();
            } catch (error) {
                addLog(`Error: ${error.message}`);
            }
        }

        async function refreshData() {
            try {
                const response = await fetch('/api/etl/schedule', { headers: authHeaders });
                const data = await response.json();
                
                // Update scheduler status
                document.getElementById('scheduler-status').textContent = 
                    data.scheduler_running ? 'Running' : 'Stopped';
                document.getElementById('scheduler-status').className = 
                    'status-badge ' + (data.scheduler_running ? 'status-success' : 'status-pending');
                document.getElementById('scheduler-jobs').textContent = data.jobs.length;

                // Update pipeline status
                Object.keys(data.pipelines).forEach(name => {
                    const pipeline = data.pipelines[name];
                    const asset = name.includes('Gold') ? 'gold' : 'silver';
                    
                    document.getElementById(`${asset}-status`).textContent = pipeline.status;
                    document.getElementById(`${asset}-status`).className = 
                        `status-badge status-${pipeline.status}`;
                    document.getElementById(`${asset}-lastrun`).textContent = 
                        pipeline.last_run ? new Date(pipeline.last_run).toLocaleTimeString() : 'Never';
                    document.getElementById(`${asset}-records`).textContent = pipeline.records;
                });
                
                addLog('Data refreshed');
            } catch (error) {
                addLog(`Refresh error: ${error.message}`);
            }
        }

        // Auto-refresh every 10 seconds
        setInterval(refreshData, 10000);
        
        // Initial load
        refreshData();
    </script>
</body>
</html>
"""


@dashboard_bp.route('/dashboard')
@token_required
def show_dashboard(current_user_email):
    """Show ETL monitoring dashboard — requires valid JWT."""
    return render_template_string(DASHBOARD_HTML)
