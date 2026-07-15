/** Human-readable labels for SHAP feature names. Single source of truth. */
export const SHAP_LABELS: Record<string, string> = {
  // Multi-timeframe features
  'htf_1h_dist_low': 'Distance from 1h low',
  'htf_1h_dist_high': 'Distance from 1h high',
  'htf_1h_momentum': '1-hour momentum',
  'htf_1h_atr': '1-hour volatility',
  'htf_1h_rsi': '1-hour RSI',
  'htf_1h_trend': '1-hour trend',
  'htf_30m_dist_low': 'Distance from 30m low',
  'htf_30m_dist_high': 'Distance from 30m high',
  'htf_30m_momentum': '30-minute momentum',
  'htf_30m_atr': '30-minute volatility',
  'htf_30m_rsi': '30-minute RSI',
  'htf_30m_trend': '30-minute trend',
  'htf_5m_dist_low': 'Distance from 5m low',
  'htf_5m_dist_high': 'Distance from 5m high',
  'htf_5m_momentum': '5-minute momentum',
  'htf_5m_atr': '5-minute volatility',
  'htf_5m_rsi': '5-minute RSI',
  'htf_5m_trend': '5-minute trend',

  // VWAP features
  'VWAPd_4': 'Short-term VWAP deviation',
  'VWAPd_16': 'Medium-term VWAP deviation',
  'VWAPd_96': 'Long-term VWAP deviation',

  // CVD features
  'CVD_4': 'Short-term order flow',
  'CVD_16': 'Medium-term order flow',
  'CVD_96': 'Long-term order flow',
  'cvd_15m': '15-minute CVD',
  'cvd_15m_slope': '15-minute CVD slope',
  'cvd_30m': '30-minute CVD',
  'cvd_30m_slope': '30-minute CVD slope',

  // Imbalance features
  'Imbal_4': 'Short-term imbalance',
  'Imbal_16': 'Medium-term imbalance',
  'Imbal_96': 'Long-term imbalance',

  // Wick features
  'Wick_4': 'Short-term wick ratio',
  'Wick_16': 'Medium-term wick ratio',
  'Wick_96': 'Long-term wick ratio',

  // Returns/Std features
  'Ret_4': 'Short-term return',
  'Ret_16': 'Medium-term return',
  'Ret_96': 'Long-term return',
  'Std_4': 'Short-term volatility',
  'Std_16': 'Medium-term volatility',
  'Std_96': 'Long-term volatility',

  // Session features
  'session_ny': 'New York session',
  'session_london': 'London session',
  'session_asia': 'Asia session',
  'session_overlap': 'Session overlap',

  // SMC features
  'fvg_bullish': 'Bullish FVG',
  'fvg_bearish': 'Bearish FVG',
  'fvg_size': 'FVG size',
  'bos_bullish': 'Bullish BOS',
  'bos_bearish': 'Bearish BOS',
  'liquidity_sweep_high': 'High liquidity sweep',
  'liquidity_sweep_low': 'Low liquidity sweep',
  'order_block_bullish': 'Bullish order block',
  'order_block_bearish': 'Bearish order block',
  'premium_discount_position': 'Premium/discount zone',
  'distance_from_equilibrium': 'Distance from fair value',
  'higher_high': 'Higher high pattern',
  'higher_low': 'Higher low pattern',
  'lower_high': 'Lower high pattern',
  'lower_low': 'Lower low pattern',
  'bullish_structure': 'Bullish structure',
  'bearish_structure': 'Bearish structure',

  // Trend features
  'trend_ema_cross': 'EMA crossover',
  'trend_price_vs_ema': 'Price vs EMA',
  'trend_adx': 'ADX trend strength',
  'trend_strength': 'Trend strength',
  'adx_14': 'ADX (14)',
  'adx_trending': 'ADX trending',
  'atr_14': 'ATR (14)',

  // Basic OHLCV
  'open': 'Open price',
  'high': 'High price',
  'low': 'Low price',
  'close': 'Close price',
  'volume': 'Trading volume',
};

export function friendlyName(raw: string): string {
  return SHAP_LABELS[raw] || raw.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}
