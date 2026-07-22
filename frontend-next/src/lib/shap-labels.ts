/** Directional, human-readable SHAP feature explanations. */
type ShapLabel = { pos: string; neg: string };

export const SHAP_LABELS: Record<string, ShapLabel> = {
  // ── Multi-timeframe distance features ──
  'htf_1h_dist_high':  { pos: 'Price pushing toward 1-hour highs',       neg: 'Price falling away from 1-hour highs' },
  'htf_1h_dist_low':   { pos: 'Price bouncing off 1-hour lows',           neg: 'Price breaking below 1-hour support' },
  'htf_1h_momentum':   { pos: 'Strong upward momentum on 1-hour',         neg: 'Downward momentum building on 1-hour' },
  'htf_1h_atr':        { pos: '1-hour volatility expanding — room to run', neg: '1-hour volatility contracting — tight range' },
  'htf_1h_rsi':        { pos: '1-hour RSI showing strength',              neg: '1-hour RSI showing weakness' },
  'htf_1h_trend':      { pos: '1-hour trend pointing upward',             neg: '1-hour trend pointing downward' },

  'htf_30m_dist_high': { pos: 'Nearing 30-minute highs — bullish pressure', neg: 'Pulling back from 30-minute highs' },
  'htf_30m_dist_low':  { pos: 'Holding above 30-minute lows — support',   neg: 'Breaking toward 30-minute lows — caution' },
  'htf_30m_momentum':  { pos: '30-minute momentum rising',                neg: '30-minute momentum fading' },
  'htf_30m_atr':       { pos: '30-minute volatility picking up',          neg: '30-minute volatility shrinking' },
  'htf_30m_rsi':       { pos: '30-minute RSI trending up',                neg: '30-minute RSI trending down' },
  'htf_30m_trend':     { pos: '30-minute trend favoring buyers',          neg: '30-minute trend favoring sellers' },

  'htf_5m_dist_high':  { pos: 'Touching 5-minute highs — short-term push', neg: 'Dropping from 5-minute highs' },
  'htf_5m_dist_low':   { pos: 'Bouncing from 5-minute lows — quick support', neg: 'Slipping below 5-minute lows' },
  'htf_5m_momentum':   { pos: '5-minute momentum surging',                neg: '5-minute momentum stalling' },
  'htf_5m_atr':        { pos: '5-minute swings widening',                 neg: '5-minute swings narrowing' },
  'htf_5m_rsi':        { pos: '5-minute RSI climbing',                    neg: '5-minute RSI dropping' },
  'htf_5m_trend':      { pos: '5-minute trend up',                        neg: '5-minute trend down' },

  // ── VWAP features ──
  'VWAPd_4':           { pos: 'Price above short-term fair value',        neg: 'Price below short-term fair value' },
  'VWAPd_16':          { pos: 'Price above medium-term fair value',       neg: 'Price below medium-term fair value' },
  'VWAPd_96':          { pos: 'Price above long-term average — overbought signal', neg: 'Price below long-term average — oversold signal' },

  // ── CVD / Order flow ──
  'CVD_4':             { pos: 'Short-term buying pressure building',      neg: 'Short-term selling pressure building' },
  'CVD_16':            { pos: 'Medium-term buying pressure — accumulation', neg: 'Medium-term selling pressure — distribution' },
  'CVD_96':            { pos: 'Long-term buyers dominating',              neg: 'Long-term sellers dominating' },
  'cvd_15m':           { pos: '15-minute order flow turning bullish',     neg: '15-minute order flow turning bearish' },
  'cvd_15m_slope':     { pos: 'Buy orders accelerating',                  neg: 'Sell orders accelerating' },
  'cvd_30m':           { pos: '30-minute order flow bullish',             neg: '30-minute order flow bearish' },
  'cvd_30m_slope':     { pos: 'Medium-term buying speeding up',           neg: 'Medium-term selling speeding up' },

  // ── Imbalance ──
  'Imbal_4':           { pos: 'Short-term buy/sell imbalance — buyers winning', neg: 'Short-term imbalance — sellers winning' },
  'Imbal_16':          { pos: 'Medium-term imbalance favoring bulls',     neg: 'Medium-term imbalance favoring bears' },
  'Imbal_96':          { pos: 'Long-term imbalance — bullish trend',      neg: 'Long-term imbalance — bearish trend' },

  // ── Wick ratios ──
  'Wick_4':            { pos: 'Short-term rejection wicks — buyers stepping in', neg: 'Short-term rejection wicks — sellers stepping in' },
  'Wick_16':           { pos: 'Medium-term buying rejections forming',    neg: 'Medium-term selling rejections forming' },
  'Wick_96':           { pos: 'Long-term buying wicks — accumulation zone', neg: 'Long-term selling wicks — distribution zone' },

  // ── Returns & Volatility ──
  'Ret_4':             { pos: 'Short-term returns positive — price rising', neg: 'Short-term returns negative — price falling' },
  'Ret_16':            { pos: 'Medium-term returns positive — uptrend',   neg: 'Medium-term returns negative — downtrend' },
  'Ret_96':            { pos: 'Long-term returns positive — bull run',    neg: 'Long-term returns negative — bear run' },
  'Std_4':             { pos: 'Short-term volatility — breakout potential', neg: 'Short-term volatility — whipsaw risk' },
  'Std_16':            { pos: 'Medium-term volatility — trending market', neg: 'Medium-term volatility — choppy market' },
  'Std_96':            { pos: 'Long-term volatility expanding',           neg: 'Long-term volatility contracting' },

  // ── Session ──
  'session_ny':        { pos: 'New York session active — institutional flow', neg: 'Outside New York hours — thinner liquidity' },
  'session_london':    { pos: 'London session active — high volume',      neg: 'Outside London hours — lower volume' },
  'session_asia':      { pos: 'Asia session active — range-bound moves',  neg: 'Outside Asia hours' },
  'session_overlap':   { pos: 'Session overlap — peak liquidity window',  neg: 'No session overlap — quieter market' },

  // ── SMC features ──
  'fvg_bullish':       { pos: 'Bullish fair value gap detected — price wants to fill upward', neg: 'No bullish FVG — no buy-side imbalance' },
  'fvg_bearish':       { pos: 'Bearish fair value gap detected — price wants to fill downward', neg: 'No bearish FVG — no sell-side imbalance' },
  'fvg_size':          { pos: 'Large FVG — strong imbalance to exploit',  neg: 'Small FVG — weaker imbalance signal' },
  'bos_bullish':       { pos: 'Bullish break of structure — trend change upward', neg: 'No bullish break — structure intact' },
  'bos_bearish':       { pos: 'Bearish break of structure — trend change downward', neg: 'No bearish break — structure intact' },
  'liquidity_sweep_high': { pos: 'High liquidity sweep — stop hunt above, may reverse down', neg: 'No high sweep — no stop hunt above' },
  'liquidity_sweep_low':  { pos: 'Low liquidity sweep — stop hunt below, may reverse up', neg: 'No low sweep — no stop hunt below' },
  'order_block_bullish':  { pos: 'Bullish order block — institutional buying zone', neg: 'No bullish order block — no buy zone' },
  'order_block_bearish':  { pos: 'Bearish order block — institutional selling zone', neg: 'No bearish order block — no sell zone' },
  'premium_discount_position': { pos: 'Price in discount zone — good buy area', neg: 'Price in premium zone — good sell area' },
  'distance_from_equilibrium': { pos: 'Price near fair value — balanced', neg: 'Price far from fair value — due for reversion' },
  'higher_high':       { pos: 'Higher high formed — uptrend confirmed',   neg: 'No higher high — uptrend not confirmed' },
  'higher_low':        { pos: 'Higher low formed — uptrend intact',       neg: 'Lower low forming — uptrend at risk' },
  'lower_high':        { pos: 'Lower high forming — downtrend may start', neg: 'Lower high confirmed — downtrend in play' },
  'lower_low':         { pos: 'Lower low formed — downtrend confirmed',   neg: 'No lower low — downtrend not confirmed' },
  'bullish_structure': { pos: 'Market structure bullish — swing highs rising', neg: 'Market structure not bullish' },
  'bearish_structure': { pos: 'Market structure bearish — swing lows falling', neg: 'Market structure not bearish' },

  // ── Trend ──
  'trend_ema_cross':     { pos: 'EMA crossover bullish — trend shifting up', neg: 'EMA crossover bearish — trend shifting down' },
  'trend_price_vs_ema':  { pos: 'Price above EMA — bullish territory',      neg: 'Price below EMA — bearish territory' },
  'trend_adx':           { pos: 'ADX confirming a strong trend',            neg: 'ADX showing a weak or fading trend' },
  'trend_strength':      { pos: 'Trend strength rising — conviction growing', neg: 'Trend strength falling — losing conviction' },
  'adx_14':              { pos: '14-period ADX — trending market',         neg: '14-period ADX — ranging market' },
  'adx_trending':        { pos: 'Market is trending — follow the move',    neg: 'Market is ranging — wait for breakout' },
  'atr_14':              { pos: '14-period ATR — wide stops needed',       neg: '14-period ATR — tight stops possible' },

  // ── Basic OHLCV ──
  'open':   { pos: 'Opening price showing strength',   neg: 'Opening price showing weakness' },
  'high':   { pos: 'Daily high acting as resistance',  neg: 'Daily high broken — breakout' },
  'low':    { pos: 'Daily low holding as support',     neg: 'Daily low broken — breakdown' },
  'close':  { pos: 'Closing price confirming strength', neg: 'Closing price confirming weakness' },
  'volume': { pos: 'Volume confirming the move — conviction', neg: 'Volume fading — move lacks conviction' },

  // ── Silver-specific 5m MTF features ──
  '5m_open':      { pos: '5-minute open holding above — micro support',  neg: '5-minute open broken below — micro breakdown' },
  '5m_high':      { pos: 'Testing 5-minute highs — scalp breakout',      neg: 'Rejected at 5-minute highs' },
  '5m_low':       { pos: 'Holding 5-minute lows — scalp support',        neg: 'Breaking 5-minute lows — scalp breakdown' },
  '5m_close':     { pos: '5-minute close strong — micro momentum up',    neg: '5-minute close weak — micro momentum down' },
  '5m_volume':    { pos: '5-minute volume surging — micro interest',     neg: '5-minute volume absent — no micro interest' },
};

/** Return a directional human label for a feature, falling back gracefully. */
export function friendlyName(raw: string, isPositive: boolean): string {
  const entry = SHAP_LABELS[raw];
  if (entry) return isPositive ? entry.pos : entry.neg;
  // Fallback: clean up the raw name
  const cleaned = raw.replace(/_/g, ' ');
  return isPositive ? `${cleaned} (bullish)` : `${cleaned} (bearish)`;
}
