# 🚀 Quick Start - Dashboard in 3 Steps

## Step 1: Setup (One-time only)

```bash
# Install API dependencies
cd ml-signals/api
pip install -r requirements.txt

# Install Frontend dependencies  
cd ../frontend
npm install
```

## Step 2: Start API

**Option A - Manual (Recommended for first time):**
```bash
cd ml-signals
python api/app/main.py
```

**Option B - Using batch file:**
```bash
tmp_rovodev_start_api.bat
```

Wait for message: `Running on http://127.0.0.1:5000`

## Step 3: Start Frontend

Open a **NEW terminal/command prompt**:

```bash
cd ml-signals/frontend
npm start
```

Browser should auto-open to `http://localhost:3000`

## ✅ Test Everything Works

From ml-signals directory:
```bash
python tmp_rovodev_test_api.py
```

This will test all API endpoints and confirm data is loading correctly.

## 📊 Dashboard Features

### Tab 1: Live Predictions
- Real-time model predictions (last 100 bars)
- Price chart with signal overlays
- Signal probability distribution
- Recent signals table

### Tab 2: Backtest Results  
- Full equity curve
- Performance metrics (Win Rate, Profit Factor, Sharpe, Drawdown)
- Session-wise breakdown (Asian, London, NY)
- Trade history table with TP/SL/Timeout indicators

### Tab 3: SHAP Analysis
- Feature importance rankings
- Top 3 features highlight
- Interactive bar charts
- Feature categorization

## 🔧 Troubleshooting

**API won't start:**
- Check Flask installed: `pip install flask flask-cors`
- Verify model exists: `ml-signals/models/enhanced_15m.pkl`
- Check port 5000 not in use

**Frontend won't start:**
- Run: `npm install` in frontend folder
- Clear cache: `npm cache clean --force`
- Check Node.js version: `node --version` (needs v14+)

**No backtest results:**
```bash
python run.py --mode backtest
```

**SHAP plot missing:**
```bash
python run.py --mode explain
```

**API returns errors:**
- Check all dependencies installed
- Verify data files exist in `Gold Dataset/` folder
- Look at API console for error messages

## 📝 Your Results

From your last run:
- ✅ Model Accuracy: **90.59%**
- ✅ Total Return: **+215.54%**
- ✅ Win Rate: **49.5%**
- ✅ Sharpe Ratio: **3.33**
- ✅ Total Trades: **1,997**

All this data is now visualized in the dashboard! 🎉

## 🌐 URLs

- API: http://localhost:5000
- Dashboard: http://localhost:3000
- API Health: http://localhost:5000/api/health

---

**Need help?** Check `DASHBOARD_README.md` for full documentation.
