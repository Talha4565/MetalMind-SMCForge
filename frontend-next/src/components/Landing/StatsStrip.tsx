export default function StatsStrip() {
  const stats = [
    { label: 'Gold Model', value: '81.3%', sub: 'Accuracy' },
    { label: 'Silver Model', value: '89.5%', sub: 'Accuracy' },
    { label: 'Features', value: '89', sub: 'SMC + Volume' },
    { label: 'Data', value: '50K+', sub: 'MT5 Spot Candles' },
    { label: 'Backtest PF', value: '6.83', sub: 'Profit Factor' },
  ];
  return (
    <section className="border-y border-border/30 bg-slate-900/30">
      <div className="max-w-7xl mx-auto px-6 py-6 grid grid-cols-2 md:grid-cols-5 gap-6">
        {stats.map((s) => (
          <div key={s.label} className="text-center">
            <p className="text-2xl md:text-3xl font-black font-mono text-card-foreground">{s.value}</p>
            <p className="text-[10px] uppercase tracking-widest text-emerald-500 mt-1">{s.label}</p>
            <p className="text-[9px] text-muted-foreground mt-0.5">{s.sub}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
