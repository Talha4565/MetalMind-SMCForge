import { Mail, ExternalLink } from 'lucide-react';

export default function ContactSection() {
  return (
    <section id="contact" className="py-24 px-6 bg-slate-900/30 border-y border-border/30">
      <div className="max-w-4xl mx-auto text-center">
        <p className="text-[10px] uppercase tracking-[0.2em] text-emerald-500 mb-3">Contact</p>
        <h2 className="text-3xl md:text-5xl font-black tracking-tight mb-8">Get in touch</h2>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <a href="mailto:talha@example.com" className="inline-flex items-center gap-2 px-8 py-4 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-xl transition-all">
            <Mail className="w-4 h-4" /> Email us
          </a>
          <a href="https://github.com/Talha4565/MetalMind-SMCForge" target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-2 px-8 py-4 border border-border hover:bg-accent/50 text-muted-foreground font-bold rounded-xl transition-all">
            <ExternalLink className="w-4 h-4" /> GitHub
          </a>
        </div>
      </div>
    </section>
  );
}
