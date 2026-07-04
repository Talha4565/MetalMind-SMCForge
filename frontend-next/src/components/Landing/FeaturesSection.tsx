import { Brain, BarChart3, Shield, Zap, Eye, TrendingUp } from 'lucide-react';

const features = [
  { icon: Brain, title: 'XGBoost ML Models', desc: 'Trained on 50K+ MT5 spot candles with 89 Smart Money Concept features.' },
  { icon: Eye, title: 'SHAP Explainability', desc: 'Every signal comes with feature importance breakdowns so you know why.' },
  { icon: BarChart3, title: 'TradingView Charts', desc: 'Live XAU/USD and XAG/USD charts with real-time spot prices from MT5.' },
  { icon: Shield, title: 'Risk Management', desc: 'Built-in position sizing, daily/monthly stops, and drawdown protection.' },
  { icon: Zap, title: 'Real-time Alerts', desc: 'Email alerts when confidence exceeds 70% on high-probability setups.' },
  { icon: TrendingUp, title: 'Walk-Forward Backtest', desc: '6-month out-of-sample results: PF 6.83 Gold, PF 50+ Silver at T=0.7.' },
];

export default function FeaturesSection() {
  return (
    <section id="features" className="py-24 px-6">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <p className="text-[10px] uppercase tracking-[0.2em] text-emerald-500 mb-3">Capabilities</p>
          <h2 className="text-3xl md:text-5xl font-black tracking-tight">Built for precision</h2>
        </div>
        <div className="grid md:grid-cols-3 gap-6">
          {features.map((f) => (
            <div key={f.title} className="p-6 rounded-2xl border border-border/50 bg-card/50 hover:bg-card transition-colors group">
              <f.icon className="w-8 h-8 text-emerald-400 mb-4 group-hover:scale-110 transition-transform" />
              <h3 className="text-sm font-bold mb-2">{f.title}</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
