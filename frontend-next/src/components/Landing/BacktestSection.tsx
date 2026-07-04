export default function BacktestSection() {
  return (
    <section id="backtest" className="py-24 px-6 bg-slate-900/30 border-y border-border/30">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <p className="text-[10px] uppercase tracking-[0.2em] text-emerald-500 mb-3">Performance</p>
          <h2 className="text-3xl md:text-5xl font-black tracking-tight">Walk-forward results</h2>
          <p className="text-muted-foreground mt-4 max-w-2xl mx-auto">6 months of out-of-sample testing on real MT5 spot data. Threshold 0.7, 1.5x ATR stop loss, 3x take profit.</p>
        </div>
        <div className="grid md:grid-cols-2 gap-8">
          <div className="p-8 rounded-2xl border border-border/50 bg-card/50">
            <p className="text-[10px] uppercase tracking-[0.2em] text-emerald-500 mb-2">Gold / XAUUSD</p>
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div><p className="text-3xl font-black font-mono">73.1%</p><p className="text-[10px] text-muted-foreground">Win Rate</p></div>
              <div><p className="text-3xl font-black font-mono text-emerald-400">6.83</p><p className="text-[10px] text-muted-foreground">Profit Factor</p></div>
              <div><p className="text-3xl font-black font-mono">0.8%</p><p className="text-[10px] text-muted-foreground">Max Drawdown</p></div>
            </div>
            <p className="text-sm text-muted-foreground">3,067 trades over 6 months. Every month profitable. $22,804 total PnL on $10K account.</p>
          </div>
          <div className="p-8 rounded-2xl border border-border/50 bg-card/50">
            <p className="text-[10px] uppercase tracking-[0.2em] text-emerald-500 mb-2">Silver / XAGUSD</p>
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div><p className="text-3xl font-black font-mono">94.7%</p><p className="text-[10px] text-muted-foreground">Win Rate</p></div>
              <div><p className="text-3xl font-black font-mono text-emerald-400">50.26</p><p className="text-[10px] text-muted-foreground">Profit Factor</p></div>
              <div><p className="text-3xl font-black font-mono">0.4%</p><p className="text-[10px] text-muted-foreground">Max Drawdown</p></div>
            </div>
            <p className="text-sm text-muted-foreground">2,411 trades over 6 months. Every month profitable. $25,252 total PnL on $10K account.</p>
          </div>
        </div>
      </div>
    </section>
  );
}
