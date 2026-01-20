# 🚀 ML Signals Dashboard

Complete React dashboard with all three components for visualizing trading signals, backtest results, and model explainability.

## ✅ What's Included

### 📈 Live Predictions Tab
- Real-time model predictions on latest data
- Price chart with trading signals overlay
- Signal probability distribution
- Model accuracy metrics
- Recent signals table with confidence levels

### 💰 Backtest Results Tab
- Complete equity curve visualization
- Performance metrics (Win Rate, Profit Factor, Sharpe Ratio, Max Drawdown)
- Session-wise performance analysis (Asian, London, NY)
- Win/Loss distribution pie chart
- Detailed trade history table
- P&L by trading session

### 🔍 SHAP Analysis Tab
- Feature importance rankings
- Top 3 most impactful features
- Interactive bar charts showing all features
- Feature details with progress bars
- SHAP summary plot visualization
- Feature categorization (Volume, Price Action, SMC)

## 🛠️ Quick Start

### First Time Setup

1. **Install dependencies:**
   ```bash
   SETUP_DASHBOARD.bat
   ```

2. **Launch dashboard:**
   ```bash
   START_DASHBOARD.bat
   ```

3. **Open browser:**
   Navigate to `http://localhost:3000`

### Manual Start (Alternative)

**Terminal 1 - API:**
```bash
cd ml-signals
python api/app/main.py
```

**Terminal 2 - Frontend:**
```bash
cd ml-signals/frontend
npm start
```

## 📊 Data Requirements

The dashboard reads from these locations:
- **Model:** `ml-signals/models/enhanced_15m.pkl`
- **Backtest Results:** `ml-signals/reports/backtest_results/latest.json`
- **SHAP Plot:** `ml-signals/reports/shap_plots/feature_importance.png`

If backtest results are missing, run:
```bash
python run.py --mode backtest
```

If SHAP analysis is missing, run:
```bash
python run.py --mode explain
```

## 🏗️ Architecture

```
ml-signals/
├── api/
│   └── app/
│       └── main.py              # Flask API server
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Main app with tabs
│   │   ├── App.css              # Styling
│   │   ├── index.js             # React entry point
│   │   └── components/
│   │       ├── LivePredictions.jsx    # Live signals view
│   │       ├── BacktestResults.jsx    # Backtest analysis
│   │       └── ShapAnalysis.jsx       # Feature importance
│   ├── public/
│   │   └── index.html
│   └── package.json
└── backtesting/
    └── engine.py                # Modified to save JSON results
```

## 🌐 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/health` | Health check |
| `GET /api/predictions/latest` | Get last 100 predictions |
| `GET /api/backtest/results` | Get backtest results JSON |
| `GET /api/shap/feature-importance` | Get SHAP feature data |
| `GET /api/shap/plot` | Get SHAP plot image |

## 🎨 Features

### Live Predictions
- ✅ Candlestick price chart with signals
- ✅ Signal probability overlay
- ✅ Model accuracy display
- ✅ Signal density metrics
- ✅ Recent signals table with timestamps

### Backtest Results
- ✅ Equity curve with timestamps
- ✅ Win/Loss pie chart
- ✅ Session performance breakdown
- ✅ Trade outcome badges (TP/SL/Timeout)
- ✅ Detailed P&L calculations
- ✅ Risk metrics (Sharpe, Drawdown)

### SHAP Analysis
- ✅ Top 3 features highlight
- ✅ Full feature ranking with visual bars
- ✅ Feature categories (Volume, Price, SMC)
- ✅ SHAP summary plot display
- ✅ Importance percentages

## 🔧 Troubleshooting

### API won't start
- Ensure Flask is installed: `pip install flask flask-cors`
- Check port 5000 is not in use
- Verify model file exists: `ml-signals/models/enhanced_15m.pkl`

### Frontend won't start
- Run `npm install` in `ml-signals/frontend/`
- Check Node.js version (requires v14+)
- Clear cache: `npm cache clean --force`

### "No backtest results found"
- Run: `python run.py --mode backtest`
- Check file exists: `ml-signals/reports/backtest_results/latest.json`

### SHAP plot not showing
- Run: `python run.py --mode explain`
- Check file exists: `ml-signals/reports/shap_plots/feature_importance.png`

## 📦 Dependencies

**Backend (Flask API):**
- flask==3.0.0
- flask-cors==4.0.0
- pandas==2.1.4
- numpy==1.26.2
- scikit-learn==1.3.2
- xgboost==2.0.3

**Frontend (React):**
- react==18.2.0
- recharts==2.10.3 (charts)
- axios==1.6.2 (API calls)
- @mui/material==5.15.0 (UI components)

## 🎯 Next Steps

1. **Customize styling** - Edit `App.css` for branding
2. **Add real-time updates** - Implement WebSocket for live data
3. **Export features** - Add CSV/PDF export buttons
4. **More charts** - Add distribution plots, correlation heatmaps
5. **Authentication** - Add login system if deploying publicly

## 📝 Notes

- Dashboard refreshes data on page load (not live streaming)
- API runs on `http://localhost:5000`
- Frontend runs on `http://localhost:3000`
- All times are displayed in local timezone
- Charts are interactive (hover for details)

---

**Built with:** React, Material-UI, Recharts, Flask, XGBoost
**Model:** Enhanced 15m Gold Trading Signals (90.59% accuracy)
