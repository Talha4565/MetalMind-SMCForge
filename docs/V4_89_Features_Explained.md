# V4 Model — 89 Features Explained

Each feature grouped by category with a one-line justification for why it matters for gold/silver intraday prediction.

---

## Base OHLCV (5 features)

| # | Feature | Justification |
|---|---------|---------------|
| 1 | `open` | Opening price — baseline for candle body analysis and gap detection |
| 2 | `high` | Highest price — used for wick analysis, FVG upper bound, liquidity sweep detection |
| 3 | `low` | Lowest price — paired with high for range, BOS lower bound, order block zones |
| 4 | `close` | Closing price — primary signal for momentum, returns, trend direction |
| 5 | `volume` | Tick volume — foundation for VWAP, CVD, imbalance, and institutional activity detection |

## Volume Microstructure — VWAP Deviation (3 features)

| # | Feature | Window | Justification |
|---|---------|--------|---------------|
| 6 | `VWAPd_4` | 4 bars (1h) | Short-term mean reversion — price far from VWAP tends to revert |
| 7 | `VWAPd_16` | 16 bars (4h) | Medium-term fair value distance — institutional anchoring level |
| 8 | `VWAPd_96` | 96 bars (24h) | Daily VWAP deviation — major support/resistance reference |

## Volume Microstructure — CVD (3 features)

| # | Feature | Window | Justification |
|---|---------|--------|---------------|
| 9 | `CVD_4` | 4 bars | Short-term order flow — buying vs selling pressure in last hour |
| 10 | `CVD_16` | 16 bars | Medium-term order flow — accumulation/distribution over 4 hours |
| 11 | `CVD_96` | 96 bars | Daily order flow — institutional positioning over full session |

## Volume Microstructure — Imbalance (3 features)

| # | Feature | Window | Justification |
|---|---------|--------|---------------|
| 12 | `Imbal_4` | 4 bars | Short-term buy/sell imbalance — directional conviction |
| 13 | `Imbal_16` | 16 bars | Medium-term imbalance — trend confirmation |
| 14 | `Imbal_96` | 96 bars | Daily imbalance — macro directional bias |

## Volume Microstructure — Wick Ratio (3 features)

| # | Feature | Window | Justification |
|---|---------|--------|---------------|
| 15 | `Wick_4` | 4 bars | Short-term rejection strength — large wicks = price level rejection |
| 16 | `Wick_16` | 16 bars | Medium-term rejection — institutional defense of levels |
| 17 | `Wick_96` | 96 bars | Daily rejection pattern — end-of-day sentiment |

## Price Dynamics — Returns (3 features)

| # | Feature | Window | Justification |
|---|---------|--------|---------------|
| 18 | `Ret_4` | 4 bars | 1-hour momentum — short-term price change rate |
| 19 | `Ret_16` | 16 bars | 4-hour momentum — medium-term trend strength |
| 20 | `Ret_96` | 96 bars | Daily momentum — session-level directional move |

## Price Dynamics — Volatility (3 features)

| # | Feature | Window | Justification |
|---|---------|--------|---------------|
| 21 | `Std_4` | 4 bars | Short-term volatility — risk level for position sizing |
| 22 | `Std_16` | 16 bars | Medium-term volatility — regime detection |
| 23 | `Std_96` | 96 bars | Daily volatility — overall market condition |

## Trading Session Flags (4 features)

| # | Feature | Justification |
|---|---------|---------------|
| 24 | `session_asia` | Asia session (00:00-08:00 UTC) — lower liquidity, different behavior |
| 25 | `session_london` | London session (08:00-16:00 UTC) — highest liquidity, institutional flows |
| 26 | `session_ny` | NY session (13:00-21:00 UTC) — overlaps London, trend continuation |
| 27 | `session_overlap` | London+NY overlap (13:00-16:00 UTC) — peak volatility, best trade window |

## SMC — Fair Value Gaps (5 features)

| # | Feature | Justification |
|---|---------|---------------|
| 28 | `fvg_bullish` | Bullish FVG detected — price gaps up, institutional buying zone |
| 29 | `fvg_bearish` | Bearish FVG detected — price gaps down, institutional selling zone |
| 30 | `fvg_size` | Gap magnitude — larger gaps = stronger institutional intent |
| 31 | `fvg_bullish_count` | Rolling count of bullish FVGs (20 bars) — accumulation pattern |
| 32 | `fvg_bearish_count` | Rolling count of bearish FVGs (20 bars) — distribution pattern |

## SMC — Break of Structure (5 features)

| # | Feature | Justification |
|---|---------|---------------|
| 33 | `bos_bullish` | Price breaks above recent swing high — trend continuation |
| 34 | `bos_bearish` | Price breaks below recent swing low — trend reversal |
| 35 | `distance_from_swing_high` | Normalized distance from nearest swing high — proximity to resistance |
| 36 | `distance_from_swing_low` | Normalized distance from nearest swing low — proximity to support |
| 37 | `bos_bullish_count` | Rolling bullish BOS count — uptrend persistence |
| 38 | `bos_bearish_count` | Rolling bearish BOS count — downtrend persistence |

## SMC — Liquidity Sweeps (4 features)

| # | Feature | Justification |
|---|---------|---------------|
| 39 | `liquidity_sweep_high` | Wick above recent high then close below — stop hunt, institutional entry |
| 40 | `liquidity_sweep_low` | Wick below recent low then close above — stop hunt, institutional entry |
| 41 | `sweep_strength` | Magnitude of the sweep — larger sweep = stronger institutional involvement |
| 42 | `liquidity_sweep_count` | Rolling sweep count — frequency of institutional activity |

## SMC — Order Blocks (4 features)

| # | Feature | Justification |
|---|---------|---------------|
| 43 | `order_block_bullish` | Strong green candle before upward move — institutional buying zone |
| 44 | `order_block_bearish` | Strong red candle before downward move — institutional selling zone |
| 45 | `order_block_strength` | Candle range relative to price — stronger = more institutional weight |
| 46 | `order_block_count` | Rolling OB count — frequency of institutional activity zones |

## SMC — Premium/Discount Zones (4 features)

| # | Feature | Justification |
|---|---------|---------------|
| 47 | `premium_discount_position` | Position within 50-bar range (0=low, 1=high) — where price sits relative to equilibrium |
| 48 | `in_premium` | Price above equilibrium — resistance zone, better for sells |
| 49 | `in_discount` | Price below equilibrium — support zone, better for buys |
| 50 | `distance_from_equilibrium` | Normalized distance from mid-range — mean reversion potential |

## SMC — Market Structure (6 features)

| # | Feature | Justification |
|---|---------|---------------|
| 51 | `higher_high` | Swing high above previous swing high — uptrend confirmation |
| 52 | `higher_low` | Swing low above previous swing low — uptrend structure |
| 53 | `lower_high` | Swing high below previous — downtrend forming |
| 54 | `lower_low` | Swing low below previous — downtrend confirmation |
| 55 | `bullish_structure` | Rolling count of HH+HL — uptrend persistence score |
| 56 | `bearish_structure` | Rolling count of LH+LL — downtrend persistence score |

## Multi-Timeframe OHLCV (10 features)

| # | Feature | Source | Justification |
|---|---------|--------|---------------|
| 57 | `30m_open` | 30m | Higher timeframe open — trend context |
| 58 | `30m_high` | 30m | HTF resistance reference |
| 59 | `30m_low` | 30m | HTF support reference |
| 60 | `30m_close` | 30m | HTF closing — trend direction |
| 61 | `30m_volume` | 30m | HTF volume — institutional participation |
| 62 | `1h_open` | 1h | Hourly open — macro trend anchor |
| 63 | `1h_high` | 1h | Hourly high — major resistance |
| 64 | `1h_low` | 1h | Hourly low — major support |
| 65 | `1h_close` | 1h | Hourly close — session trend |
| 66 | `1h_volume` | 1h | Hourly volume — institutional flow magnitude |

## HTF Indicators — 30m (6 features)

| # | Feature | Justification |
|---|---------|---------------|
| 67 | `htf_30m_trend` | 30m EMA crossover direction — medium-term trend |
| 68 | `htf_30m_atr` | 30m ATR normalized — volatility regime |
| 69 | `htf_30m_rsi` | 30m RSI — overbought/oversold on higher timeframe |
| 70 | `htf_30m_dist_high` | Distance from 30m 20-bar high — resistance proximity |
| 71 | `htf_30m_dist_low` | Distance from 30m 20-bar low — support proximity |
| 72 | `htf_30m_momentum` | 30m 5-bar momentum — short-term HTF direction |

## HTF Indicators — 1h (6 features)

| # | Feature | Justification |
|---|---------|---------------|
| 73 | `htf_1h_trend` | 1h EMA crossover — macro trend direction |
| 74 | `htf_1h_atr` | 1h ATR normalized — daily volatility regime |
| 75 | `htf_1h_rsi` | 1h RSI — daily overbought/oversold |
| 76 | `htf_1h_dist_high` | Distance from 1h 20-bar high — daily resistance |
| 77 | `htf_1h_dist_low` | Distance from 1h 20-bar low — daily support |
| 78 | `htf_1h_momentum` | 1h 5-bar momentum — daily directional strength |

## V4-Specific Features (11 features)

| # | Feature | Justification |
|---|---------|---------------|
| 79 | `cvd_15m` | 15m CVD — primary timeframe order flow |
| 80 | `cvd_15m_slope` | 15m CVD slope — order flow acceleration/deceleration |
| 81 | `cvd_30m` | 30m CVD — medium-term order flow |
| 82 | `cvd_30m_slope` | 30m CVD slope — medium-term flow momentum |
| 83 | `adx_14` | 14-period ADX — trend strength measurement |
| 84 | `adx_trending` | ADX > 25 binary — whether market is trending or ranging |
| 85 | `atr_14` | 14-period ATR — volatility for TP/SL sizing |
| 86 | `trend_ema_cross` | EMA20 vs EMA50 crossover — primary trend direction (1=up, 0=down) |
| 87 | `trend_price_vs_ema` | Price deviation from EMA20 — overextension signal |
| 88 | `trend_adx` | Normalized ADX — trend conviction (0-1 scale) |
| 89 | `trend_strength` | EMA spread normalized — how strong the current trend is |

---

## Trend Filter Logic (V4 Signal Generation)

```
Input: model probability (proba), trend_ema_cross (1 or 0)

BUY when:
  - trend_ema_cross == 1 (EMA20 > EMA50, uptrend)
  - AND proba >= 0.5 (model predicts up)
  - AND max(proba, 1-proba) >= 0.65 (confidence threshold)

SELL when:
  - trend_ema_cross == 0 (EMA20 < EMA50, downtrend)
  - AND proba < 0.5 (model predicts down)
  - AND max(proba, 1-proba) >= 0.65 (confidence threshold)

HOLD otherwise
```

**Why this filter works:** Three independent conditions must align — trend direction (EMA), model conviction (probability), and confidence threshold (65%). This eliminates weak signals where the model is uncertain or the trend contradicts the prediction.
