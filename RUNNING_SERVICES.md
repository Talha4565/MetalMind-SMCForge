# ML-Signals Running Services

## ✅ Services Status

Both the backend and frontend are now running successfully!

### Backend (Flask API)
- **URL**: http://localhost:5000
- **Status**: ✅ Healthy
- **Models Loaded**: 
  - Gold Model: ✅ Loaded
  - Silver Model: ✅ Loaded

### Frontend (React Dashboard)
- **URL**: http://localhost:3000
- **Status**: ✅ Running

---

## 🚀 Quick Start Commands

### Start Both Services
```powershell
cd ml-signals
.\start_all.ps1
```

### Start Backend Only
```powershell
cd ml-signals
.\start_backend.ps1
```

### Start Frontend Only
```powershell
cd ml-signals
.\start_frontend.ps1
```

---

## 📡 API Endpoints

All API endpoints require authentication token (except /api/health).

### Health Check
```
GET http://localhost:5000/api/health
```

### Predictions
```
GET http://localhost:5000/api/predictions/latest?asset=gold&limit=100
GET http://localhost:5000/api/predictions/latest?asset=silver&limit=100
```

### Backtest
```
GET http://localhost:5000/api/backtest/results?asset=gold
POST http://localhost:5000/api/backtest/run
```

### SHAP Analysis
```
GET http://localhost:5000/api/shap/feature-importance
GET http://localhost:5000/api/shap/plot
```

### Configuration
```
GET http://localhost:5000/api/config
POST http://localhost:5000/api/config
```

### Model Info
```
GET http://localhost:5000/api/models/info?asset=gold
GET http://localhost:5000/api/models/info?asset=silver
```

---

## 🛑 Stopping Services

Simply close the two PowerShell windows that were opened when you started the services.

Or use Task Manager to stop processes:
- Look for "python" process running `app/main.py`
- Look for "node" process running React

---

## 📝 Notes

- The backend runs on port 5000
- The frontend runs on port 3000
- Both models (Gold and Silver) are successfully loaded
- The frontend will automatically connect to the backend API
- CORS is enabled for cross-origin requests

---

## 🔧 Troubleshooting

### Backend won't start
1. Check if port 5000 is already in use
2. Ensure all Python dependencies are installed: `pip install -r api/requirements.txt`
3. Install missing packages: `pip install flask-limiter werkzeug`

### Frontend won't start
1. Check if port 3000 is already in use
2. Ensure Node.js dependencies are installed: `cd frontend && npm install`
3. Clear npm cache if needed: `npm cache clean --force`

### Models not loading
1. Train the models first:
   - Gold: `python models/train_enhanced.py`
   - Silver: `python models/train_silver_model.py`
2. Check that model files exist:
   - `models/enhanced_15m.pkl`
   - `models/processed/silver_model_enhanced.pkl`
