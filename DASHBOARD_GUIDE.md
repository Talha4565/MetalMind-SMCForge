# 🎨 Dashboard Visualization Guide

## 🌐 Access Your Dashboard

**URL:** http://localhost:3000

The dashboard should be opening in your browser now!

---

## 📊 What to Explore in Each Tab

### Tab 1: 📈 Live Predictions

**What You'll See:**

1. **Top Stats Cards** (Purple gradient card + 3 white cards)
   - Model Accuracy: **90.6%** (purple card with checkmark icon)
   - Total Signals: **13** (in last 100 bars)
   - Signal Density: **~3.3/hr** (signals per hour)
   - Latest Price: Current XAU/USD price

2. **Price Chart with Signals** (Main chart)
   - Blue line showing gold price movement
   - **Green circles** = Trading signals (where model predicts long)
   - Hover over points to see details
   - X-axis: Time, Y-axis: Price ($)

3. **Signal Probability Chart** (Below price chart)
   - Orange line showing model confidence over time
   - Dashed line at 50% = decision threshold
   - Higher = stronger signal confidence

4. **Recent Signals Table** (Bottom)
   - Last 10 signals with timestamps
   - Price at signal time
   - Confidence level with progress bar
   - "LONG SIGNAL" green badges

**What to Check:**
- ✅ Charts load and display properly
- ✅ Green markers appear on price chart
- ✅ Hover tooltips work
- ✅ Signal probability shows variation

---

### Tab 2: 💰 Backtest Results

**What You'll See:**

1. **Summary Cards** (Top row)
   - **Total Return:** +215.5% (green gradient card)
   - **Win Rate:** 49.5% (989 wins / 1997 trades)
   - **Profit Factor:** 1.63 (avg win / avg loss ratio)
   - **Max Drawdown:** -9.26% (worst equity dip)

2. **Equity Curve Chart** (Large green line)
   - Shows portfolio growing from $1,000 → $3,155.37
   - Smooth upward trend with some drawdowns
   - Hover to see exact equity at each point

3. **Session Performance Charts** (2 charts side-by-side)
   - **Bar Chart (Left):** P&L by trading session
     - London: $88.37 (407 trades)
     - NY: $2,067.00 (1590 trades) - Best performer!
     - Asian: $0 (no trades during filter)
   
   - **Pie Chart (Right):** Win/Loss distribution
     - Green slice: 989 wins (49.5%)
     - Red slice: 1008 losses (50.5%)

4. **Session Statistics Table**
   - Breakdown of trades, P&L, avg P&L, and win rate per session

5. **Recent Trades Table** (Bottom)
   - Last 20 trades with full details
   - Color-coded P&L (green = profit, red = loss)
   - Badges: TP (Take Profit), SL (Stop Loss), TO (Timeout)

**What to Check:**
- ✅ Equity curve shows upward trend
- ✅ NY session dominates (best P&L)
- ✅ Trade table shows TP/SL badges
- ✅ All numbers match your backtest run

---

### Tab 3: 🔍 SHAP Analysis

**What You'll See:**

1. **Info Box** (Blue alert at top)
   - Explanation of what SHAP means
   - "SHapley Additive exPlanations"

2. **Top 3 Features** (Purple gradient cards)
   - #1: **vwap_distance_5m** - 15% importance
   - #2: **vwap_distance_15m** - 12% importance
   - #3: **volume_imbalance** - 10% importance
   - Each with progress bar showing impact

3. **Feature Importance Bar Chart**
   - Horizontal bars ranking all 10 features
   - Colored bars (purple, pink, blue gradient)
   - Y-axis: Feature names, X-axis: Importance %

4. **Feature Details List**
   - All features ranked #1-#10
   - Top 3 highlighted in blue
   - Progress bars showing relative importance

5. **SHAP Summary Plot** (If available)
   - Image showing feature impacts
   - Located at: `reports/shap_plots/feature_importance.png`

6. **Feature Categories** (3 colored boxes at bottom)
   - 📊 Volume Features (blue box)
   - 📈 Price Action Features (green box)
   - 🎯 SMC Features (yellow box)

**What to Check:**
- ✅ Top 3 features clearly highlighted
- ✅ Bar chart displays correctly
- ✅ All features ranked properly
- ✅ Category boxes show feature groupings

---

## 🎯 Quick Navigation Tips

1. **Switch Tabs:** Click tab names at top ("Live Predictions" / "Backtest Results" / "SHAP Analysis")

2. **Interactive Charts:** 
   - Hover over any chart for details
   - Charts are responsive and animate

3. **Scroll Down:** Each tab has multiple sections

4. **Refresh Data:** Reload page to refresh predictions (they load from live data)

---

## ✅ Success Checklist

As you explore, verify:

- [ ] All three tabs load without errors
- [ ] Charts display with proper data
- [ ] Top stats cards show correct numbers
- [ ] Equity curve shows $1,000 → $3,155.37 growth
- [ ] Trade table shows TP/SL badges
- [ ] SHAP rankings show top 3 features
- [ ] No console errors (press F12 to check)
- [ ] Responsive design (try resizing window)

---

## 🐛 If Something Looks Wrong

**Charts not showing:**
- Check browser console (F12) for errors
- Verify API is running at http://localhost:5000
- Try refreshing the page

**"No backtest results found":**
- API endpoint issue
- Check API terminal for error messages

**Styling looks broken:**
- Clear browser cache (Ctrl+Shift+R)
- Check `App.css` loaded properly

**Tab switching doesn't work:**
- JavaScript error - check console
- Verify all component files exist

---

## 🎨 What Makes This Dashboard Special

✨ **Material-UI Design** - Professional, modern UI components
📊 **Recharts Library** - Interactive, animated charts
🎯 **Real Model Data** - Your actual 90.6% accuracy model
💰 **Real Backtest Results** - Your +215% return performance
🔍 **SHAP Explainability** - Understand what drives predictions
📱 **Responsive Layout** - Works on different screen sizes

---

## 🚀 Next Steps After Exploring

1. **Customize Colors:** Edit `frontend/src/App.css`
2. **Add Features:** Export to CSV, date filters, more charts
3. **Deploy:** Docker containerization for production
4. **Real-time Updates:** Add WebSocket for live data streaming
5. **Mobile Optimization:** Enhance responsive design

---

**Enjoy exploring your dashboard!** 🎉

If you see all three tabs loading with data, **the dashboard is working perfectly!**
