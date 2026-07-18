'use client';

import { useState, useEffect } from 'react';
import DashboardLayout from '@/components/Common/DashboardLayout';
import TerminalCard, { TerminalStatRow, TerminalSectionHeader } from '@/components/Common/TerminalCard';
import { Input } from '@/components/ui/input';
import { apiClient } from '@/lib/api-client';
import { AssetType } from '@/lib/api-types';
import { Calculator, TrendingUp, TrendingDown, Shield, AlertTriangle, DollarSign, BarChart3 } from 'lucide-react';
import { cn } from '@/lib/utils';

const TRADING_PARAMS = {
  gold: { tp_pct: 0.0045, sl_pct: 0.0015, lot_size: 100, pip_value: 0.01 },
  silver: { tp_pct: 0.003, sl_pct: 0.001, lot_size: 5000, pip_value: 0.001 },
};

const RISK_PROFILES = {
  conservative: { risk_pct: 0.01, label: 'Conservative', desc: '1% risk/trade' },
  balanced: { risk_pct: 0.02, label: 'Balanced', desc: '2% risk/trade' },
  aggressive: { risk_pct: 0.03, label: 'Aggressive', desc: '3% risk/trade' },
};

interface RiskCalculation {
  riskDollars: number; riskPercent: number; positionSize: number;
  lotSize: number; stopLossPrice: number; takeProfitPrice: number;
  riskReward: number; marginRequired: number;
}

function calculateRisk(balance: number, price: number, asset: AssetType, riskProfile: keyof typeof RISK_PROFILES): RiskCalculation | null {
  if (balance <= 0 || price <= 0) return null;
  const params = TRADING_PARAMS[asset];
  const profile = RISK_PROFILES[riskProfile];
  const riskDollars = balance * profile.risk_pct;
  const riskPercent = profile.risk_pct * 100;
  const positionSize = riskDollars / (price * params.sl_pct);
  const lotSize = positionSize / params.lot_size;
  const stopLossPrice = price * (1 - params.sl_pct);
  const takeProfitPrice = price * (1 + params.tp_pct);
  const riskReward = params.tp_pct / params.sl_pct;
  const marginRequired = (positionSize * price) * 0.05;
  return { riskDollars, riskPercent, positionSize, lotSize, stopLossPrice, takeProfitPrice, riskReward, marginRequired };
}

export default function RiskPage() {
  const [balance, setBalance] = useState(1000);
  const [activeAsset, setActiveAsset] = useState<AssetType>('gold');
  const [riskProfile, setRiskProfile] = useState<keyof typeof RISK_PROFILES>('balanced');
  const [livePrice, setLivePrice] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    const fetchPrice = async () => {
      try {
        const data = await apiClient.getLivePrice(activeAsset);
        if (mounted) { setLivePrice(data.price); setIsLoading(false); }
      } catch { if (mounted) setIsLoading(false); }
    };
    fetchPrice();
    const interval = setInterval(fetchPrice, 15000);
    return () => { mounted = false; clearInterval(interval); };
  }, [activeAsset]);

  const calc = livePrice ? calculateRisk(balance, livePrice, activeAsset, riskProfile) : null;

  return (
    <DashboardLayout>
      <div className="space-y-6 p-4">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-black tracking-tight text-terminal-value font-mono">RISK CALCULATOR</h1>
            <p className="text-terminal-label text-xs mt-1 font-mono tracking-wider">Position sizing · stop loss · take profit</p>
          </div>
          <div className="flex border border-terminal-rule">
            {(['gold', 'silver'] as AssetType[]).map((a) => (
              <button key={a} onClick={() => setActiveAsset(a)}
                className={cn('px-4 py-1.5 text-[9px] font-mono font-bold uppercase tracking-widest transition-all border-r border-terminal-rule last:border-0',
                  activeAsset === a ? 'bg-terminal-hold text-black' : 'text-terminal-label hover:text-terminal-value')}>
                {a === 'gold' ? 'XAU/USD' : 'XAG/USD'}
              </button>
            ))}
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-[1.2fr_1fr]">
          {/* Left column */}
          <div className="space-y-4">
            {/* Balance */}
            <TerminalCard title="ACCOUNT BALANCE" code="BAL">
              <div className="flex items-center gap-3">
                <span className="text-terminal-label font-mono text-lg">$</span>
                <Input type="number" value={balance} onChange={(e) => setBalance(Number(e.target.value) || 0)}
                  className="text-2xl font-mono font-black h-14 bg-terminal-panel border-terminal-rule text-terminal-value rounded-none" min={0} step={100} />
              </div>
            </TerminalCard>

            {/* Risk Profile */}
            <TerminalCard title="RISK PROFILE" code="RSK">
              <div className="grid grid-cols-3 gap-3">
                {(Object.entries(RISK_PROFILES) as [keyof typeof RISK_PROFILES, typeof RISK_PROFILES[keyof typeof RISK_PROFILES]][]).map(([key, profile]) => (
                  <button key={key} onClick={() => setRiskProfile(key)}
                    className={cn('p-3 border text-left transition-all font-mono',
                      riskProfile === key ? 'border-terminal-hold bg-terminal-hold/10 text-terminal-value' : 'border-terminal-rule bg-terminal-panel text-terminal-label hover:border-terminal-label')}>
                    <p className="font-bold text-[10px]">{profile.label}</p>
                    <p className="text-[8px] mt-1 opacity-70">{profile.desc}</p>
                  </button>
                ))}
              </div>
            </TerminalCard>

            {/* Current Price */}
            <TerminalCard title="CURRENT PRICE" code="PRC">
              {isLoading ? (
                <div className="h-12 bg-terminal-panel border border-terminal-rule animate-pulse" />
              ) : (
                <p className="text-3xl font-black font-mono text-terminal-value">
                  ${livePrice?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '—'}
                </p>
              )}
              <p className="text-[9px] font-mono text-terminal-label mt-1">{activeAsset === 'gold' ? 'XAU/USD' : 'XAG/USD'} · Live MT5</p>
            </TerminalCard>

            {/* Risk Parameters */}
            <TerminalCard title="RISK PARAMETERS" code="PAR">
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 border border-terminal-rule bg-terminal-panel">
                  <p className="text-[9px] font-mono text-terminal-label">Take Profit</p>
                  <p className="font-mono font-bold text-terminal-buy text-sm">{(TRADING_PARAMS[activeAsset].tp_pct * 100).toFixed(2)}%</p>
                </div>
                <div className="p-3 border border-terminal-rule bg-terminal-panel">
                  <p className="text-[9px] font-mono text-terminal-label">Stop Loss</p>
                  <p className="font-mono font-bold text-terminal-sell text-sm">{(TRADING_PARAMS[activeAsset].sl_pct * 100).toFixed(2)}%</p>
                </div>
                <div className="p-3 border border-terminal-rule bg-terminal-panel">
                  <p className="text-[9px] font-mono text-terminal-label">Lot Size</p>
                  <p className="font-mono font-bold text-terminal-value text-sm">{TRADING_PARAMS[activeAsset].lot_size} oz</p>
                </div>
                <div className="p-3 border border-terminal-rule bg-terminal-panel">
                  <p className="text-[9px] font-mono text-terminal-label">Margin (5%)</p>
                  <p className="font-mono font-bold text-terminal-value text-sm">${calc ? calc.marginRequired.toFixed(2) : '—'}</p>
                </div>
              </div>
            </TerminalCard>
          </div>

          {/* Right: Results */}
          <div className="space-y-4">
            {calc ? (
              <>
                <TerminalCard title="TRADE CALCULATION" code="CAL">
                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-3 border border-terminal-rule bg-terminal-panel">
                      <p className="text-[8px] font-mono font-bold uppercase tracking-widest text-terminal-label">Risk/Trade</p>
                      <p className="text-xl font-black font-mono text-terminal-value mt-1">${calc.riskDollars.toFixed(2)}</p>
                      <p className="text-[8px] font-mono text-terminal-label">{calc.riskPercent.toFixed(1)}% of balance</p>
                    </div>
                    <div className="p-3 border border-terminal-rule bg-terminal-panel">
                      <p className="text-[8px] font-mono font-bold uppercase tracking-widest text-terminal-label">Position</p>
                      <p className="text-xl font-black font-mono text-terminal-value mt-1">{calc.positionSize.toFixed(4)}</p>
                      <p className="text-[8px] font-mono text-terminal-label">troy oz</p>
                    </div>
                    <div className="p-3 border border-terminal-rule bg-terminal-panel">
                      <p className="text-[8px] font-mono font-bold uppercase tracking-widest text-terminal-label">Lot Size</p>
                      <p className="text-xl font-black font-mono text-terminal-value mt-1">{calc.lotSize.toFixed(4)}</p>
                      <p className="text-[8px] font-mono text-terminal-label">standard lots</p>
                    </div>
                    <div className="p-3 border border-terminal-rule bg-terminal-panel">
                      <p className="text-[8px] font-mono font-bold uppercase tracking-widest text-terminal-label">R/R</p>
                      <p className={cn('text-xl font-black font-mono mt-1', calc.riskReward >= 2 ? 'text-terminal-buy' : calc.riskReward >= 1.5 ? 'text-terminal-hold' : 'text-terminal-sell')}>
                        1:{calc.riskReward.toFixed(1)}
                      </p>
                      <p className="text-[8px] font-mono text-terminal-label">{calc.riskReward >= 2 ? 'Excellent' : calc.riskReward >= 1.5 ? 'Acceptable' : 'Poor'}</p>
                    </div>
                  </div>
                </TerminalCard>

                <TerminalCard title="PRICE LEVELS" code="LVL">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between p-3 border border-terminal-buy/20 bg-terminal-buy/5">
                      <div className="flex items-center gap-2"><TrendingUp className="w-4 h-4 text-terminal-buy" /><span className="text-xs font-mono font-bold text-terminal-value">Take Profit</span></div>
                      <span className="font-mono font-bold text-terminal-buy">${calc.takeProfitPrice.toFixed(2)}</span>
                    </div>
                    <div className="flex items-center justify-between p-3 border border-terminal-rule bg-terminal-panel">
                      <div className="flex items-center gap-2"><DollarSign className="w-4 h-4 text-terminal-label" /><span className="text-xs font-mono font-bold text-terminal-value">Entry</span></div>
                      <span className="font-mono font-bold text-terminal-value">${livePrice?.toFixed(2)}</span>
                    </div>
                    <div className="flex items-center justify-between p-3 border border-terminal-sell/20 bg-terminal-sell/5">
                      <div className="flex items-center gap-2"><TrendingDown className="w-4 h-4 text-terminal-sell" /><span className="text-xs font-mono font-bold text-terminal-value">Stop Loss</span></div>
                      <span className="font-mono font-bold text-terminal-sell">${calc.stopLossPrice.toFixed(2)}</span>
                    </div>
                  </div>
                </TerminalCard>

                <div className="border border-terminal-hold/20 bg-terminal-hold/5 p-4">
                  <div className="flex items-center gap-2 mb-3"><Shield className="w-4 h-4 text-terminal-hold" /><span className="text-xs font-mono font-bold text-terminal-value">TRADE SUMMARY</span></div>
                  <div className="grid grid-cols-2 gap-3 text-xs font-mono">
                    <div><p className="text-terminal-label">You risk</p><p className="font-bold text-terminal-value">${calc.riskDollars.toFixed(2)} ({calc.riskPercent.toFixed(1)}%)</p></div>
                    <div><p className="text-terminal-label">Position</p><p className="font-bold text-terminal-value">{calc.positionSize.toFixed(4)} oz</p></div>
                    <div><p className="text-terminal-label">If TP hits</p><p className="font-bold text-terminal-buy">+${(calc.riskDollars * calc.riskReward).toFixed(2)}</p></div>
                    <div><p className="text-terminal-label">If SL hits</p><p className="font-bold text-terminal-sell">-${calc.riskDollars.toFixed(2)}</p></div>
                  </div>
                </div>
              </>
            ) : (
              <TerminalCard title="TRADE CALCULATION" code="CAL">
                <p className="font-mono text-xs text-terminal-label text-center py-8">
                  {isLoading ? 'Loading price data...' : 'Enter a valid balance to calculate position size.'}
                </p>
              </TerminalCard>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
