export default function AboutSection() {
  return (
    <section id="about" className="py-24 px-6">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-16">
          <p className="text-[10px] uppercase tracking-[0.2em] text-emerald-500 mb-3">About</p>
          <h2 className="text-3xl md:text-5xl font-black tracking-tight">What is MetalMind?</h2>
        </div>
        <div className="space-y-6 text-muted-foreground leading-relaxed">
          <p>
            MetalMind SMCForge is a machine learning trading system that combines Smart Money Concepts
            (SMC) with XGBoost classification to generate high-confidence trade signals for gold and silver.
          </p>
          <p>
            Unlike black-box models, every prediction comes with SHAP explainability — you see exactly
            which features (FVG, BOS, liquidity sweeps, order blocks) drove the signal.
          </p>
          <p>
            The system uses real MT5 spot data (XAUUSD, XAGUSD), not futures. Models are retrained
            daily on 50K+ candles spanning 2+ years of market history.
          </p>
          <p className="text-sm text-muted-foreground/60 border-t border-border/30 pt-6">
            Built as a Final Year Project. Not financial advice. Past performance does not guarantee future results.
          </p>
        </div>
      </div>
    </section>
  );
}
