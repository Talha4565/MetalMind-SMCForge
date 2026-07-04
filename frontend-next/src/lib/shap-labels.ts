/** Human-readable labels for SHAP feature names. Single source of truth. */
export const SHAP_LABELS: Record<string, string> = {
  'htf_1h_dist_low': 'Distance from recent low',
  'htf_1h_dist_high': 'Distance from recent high',
  'htf_1h_momentum': '1-hour momentum',
  'htf_1h_atr': '1-hour volatility',
  'premium_discount_position': 'Premium/discount zone',
  'distance_from_equilibrium': 'Distance from fair value',
  'VWAPd_4': 'Short-term price deviation',
  'VWAPd_16': 'Medium-term price deviation',
  'VWAPd_96': 'Long-term price deviation',
  'CVD_4': 'Short-term order flow',
  'CVD_16': 'Medium-term order flow',
  'CVD_96': 'Long-term order flow',
  'session_ny': 'New York session',
  'session_london': 'London session',
  'session_asia': 'Asia session',
  'session_overlap': 'Session overlap',
  'Std_4': 'Short-term variability',
  'Std_16': 'Medium-term variability',
  'Std_96': 'Long-term variability',
  'Ret_4': 'Short-term return',
  'Ret_16': 'Medium-term return',
  'Ret_96': 'Long-term return',
  'Imbal_4': 'Short-term imbalance',
  'Imbal_16': 'Medium-term imbalance',
  'Imbal_96': 'Long-term imbalance',
  'Wick_4': 'Short-term wick ratio',
  'Wick_16': 'Medium-term wick ratio',
  'Wick_96': 'Long-term wick ratio',
  'close': 'Current price',
  'high': 'Session high',
  'low': 'Session low',
  'volume': 'Trading volume',
};

export function friendlyName(raw: string): string {
  return SHAP_LABELS[raw] || raw.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}
