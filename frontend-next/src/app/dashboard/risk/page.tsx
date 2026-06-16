'use client';

import { useState, useEffect } from 'react';
import DashboardLayout from '@/components/Common/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { apiClient } from '@/lib/api-client';
import { AssetType } from '@/lib/api-types';
import {
  Calculator,
  TrendingUp,
  TrendingDown,
  Shield,
  AlertTriangle,
  DollarSign,
  BarChart3,
  RefreshCcw,
} from 'lucide-react';
import { cn } from '@/lib/utils';

// Trading parameters from config
const TRADING_PARAMS = {
  gold: { tp_pct: 0.0045, sl_pct: 0.0015, lot_size: 100, pip_value: 0.01 },
  silver: { tp_pct: 0.003, sl_pct: 0.001, lot_size: 5000, pip_value: 0.001 },
};

const RISK_PROFILES = {
  conservative: { risk_pct: 0.01, label: 'Conservative', desc: '1% risk per trade' },
  balanced: { risk_pct: 0.02, label: 'Balanced', desc: '2% risk per trade' },
  aggressive: { risk_pct: 0.03, label: 'Aggressive', desc: '3% risk per trade' },
};

interface RiskCalculation {
  riskDollars: number;
  riskPercent: number;
  positionSize: number;
  lotSize: number;
  stopLossPrice: number;
  takeProfitPrice: number;
  riskReward: number;
  marginRequired: number;
}

function calculateRisk(
  balance: number,
  price: number,
  asset: AssetType,
  riskProfile: keyof typeof RISK_PROFILES
): RiskCalculation | null {
  if (balance <= 0 || price <= 0) return null;

  const params = TRADING_PARAMS[asset];
  const profile = RISK_PROFILES[riskProfile];

  const riskDollars = balance * profile.risk_pct;
  const riskPercent = profile.risk_pct * 100;

  // Position size = risk $ / (entry price × stop loss %)
  const positionSize = riskDollars / (price * params.sl_pct);

  // Lot size (gold: 1 lot = 100 oz, silver: 1 lot = 5000 oz)
  const lotSize = positionSize / params.lot_size;

  // Stop loss and take profit prices
  const stopLossPrice = price * (1 - params.sl_pct);
  const takeProfitPrice = price * (1 + params.tp_pct);

  // Risk/reward ratio
  const riskReward = params.tp_pct / params.sl_pct;

  // Margin required (assuming 5% margin for demonstration)
  const marginRequired = (positionSize * price) * 0.05;

  return {
    riskDollars,
    riskPercent,
    positionSize,
    lotSize,
    stopLossPrice,
    takeProfitPrice,
    riskReward,
    marginRequired,
  };
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
        if (mounted) {
          setLivePrice(data.price);
          setIsLoading(false);
        }
      } catch {
        if (mounted) setIsLoading(false);
      }
    };
    fetchPrice();
    const interval = setInterval(fetchPrice, 15000);
    return () => { mounted = false; clearInterval(interval); };
  }, [activeAsset]);

  const calc = livePrice ? calculateRisk(balance, livePrice, activeAsset, riskProfile) : null;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="rounded-xl border border-border bg-card p-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-muted-foreground">Risk calculator</p>
              <h1 className="mt-1 text-3xl font-black text-card-foreground">Position sizing</h1>
              <p className="mt-1 text-sm text-muted-foreground">
                Calculate trade size, stop loss, take profit, and risk/reward ratio.
              </p>
            </div>

            {/* Asset toggle */}
            <div className="flex bg-background p-1 rounded-lg border border-border">
              {(['gold', 'silver'] as AssetType[]).map((asset) => (
                <button
                  key={asset}
                  onClick={() => setActiveAsset(asset)}
                  className={cn(
                    "px-5 py-2 rounded-md text-xs font-bold uppercase tracking-widest transition-all",
                    activeAsset === asset
                      ? "bg-card text-card-foreground shadow-sm"
                      : "text-muted-foreground hover:text-foreground"
                  )}
                >
                  {asset}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-[1.2fr_1fr]">
          {/* Left: Inputs + Results */}
          <div className="space-y-6">
            {/* Account Balance */}
            <Card className="bg-card border-border">
              <CardHeader className="pb-4">
                <CardTitle className="text-sm font-bold text-card-foreground flex items-center gap-2">
                  <DollarSign className="w-4 h-4 text-emerald-500" />
                  Account balance
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-3">
                  <span className="text-muted-foreground text-lg">$</span>
                  <Input
                    type="number"
                    value={balance}
                    onChange={(e) => setBalance(Number(e.target.value) || 0)}
                    className="text-2xl font-mono font-black h-14 bg-background border-border text-card-foreground"
                    min={0}
                    step={100}
                  />
                </div>
              </CardContent>
            </Card>

            {/* Risk Profile */}
            <Card className="bg-card border-border">
              <CardHeader className="pb-4">
                <CardTitle className="text-sm font-bold text-card-foreground flex items-center gap-2">
                  <Shield className="w-4 h-4 text-emerald-500" />
                  Risk profile
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-3">
                  {(Object.entries(RISK_PROFILES) as [keyof typeof RISK_PROFILES, typeof RISK_PROFILES[keyof typeof RISK_PROFILES]][]).map(([key, profile]) => (
                    <button
                      key={key}
                      onClick={() => setRiskProfile(key)}
                      className={cn(
                        "p-4 rounded-xl border text-left transition-all",
                        riskProfile === key
                          ? "border-emerald-500 bg-emerald-500/10 text-card-foreground"
                          : "border-border bg-background text-muted-foreground hover:border-slate-600"
                      )}
                    >
                      <p className="font-bold text-sm">{profile.label}</p>
                      <p className="text-xs mt-1 opacity-70">{profile.desc}</p>
                    </button>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Current Price */}
            <Card className="bg-card border-border">
              <CardHeader className="pb-4">
                <CardTitle className="text-sm font-bold text-card-foreground flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-emerald-500" />
                  Current price
                </CardTitle>
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <div className="h-12 bg-background rounded-lg animate-pulse" />
                ) : (
                  <p className="text-3xl font-black font-mono text-card-foreground">
                    ${livePrice?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '—'}
                  </p>
                )}
                <p className="text-xs text-muted-foreground mt-1">
                  {activeAsset === 'gold' ? 'XAU/USD' : 'XAG/USD'} • Live from Yahoo Finance
                </p>
              </CardContent>
            </Card>

            {/* Risk Parameters */}
            <Card className="bg-card border-border">
              <CardHeader className="pb-4">
                <CardTitle className="text-sm font-bold text-card-foreground flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-500" />
                  Risk parameters
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div className="p-3 rounded-lg bg-background">
                    <p className="text-muted-foreground text-xs">Take profit</p>
                    <p className="font-bold text-card-foreground">{(TRADING_PARAMS[activeAsset].tp_pct * 100).toFixed(2)}%</p>
                  </div>
                  <div className="p-3 rounded-lg bg-background">
                    <p className="text-muted-foreground text-xs">Stop loss</p>
                    <p className="font-bold text-card-foreground">{(TRADING_PARAMS[activeAsset].sl_pct * 100).toFixed(2)}%</p>
                  </div>
                  <div className="p-3 rounded-lg bg-background">
                    <p className="text-muted-foreground text-xs">Lot size</p>
                    <p className="font-bold text-card-foreground">{TRADING_PARAMS[activeAsset].lot_size} {activeAsset === 'gold' ? 'oz' : 'oz'}</p>
                  </div>
                  <div className="p-3 rounded-lg bg-background">
                    <p className="text-muted-foreground text-xs">Margin (5%)</p>
                    <p className="font-bold text-card-foreground">${calc ? calc.marginRequired.toFixed(2) : '—'}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right: Results */}
          <div className="space-y-6">
            {calc ? (
              <>
                {/* Risk Summary */}
                <Card className="bg-card border-border border-l-4 border-l-emerald-500">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-bold text-card-foreground flex items-center gap-2">
                      <Calculator className="w-4 h-4 text-emerald-500" />
                      Trade calculation
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="p-4 rounded-xl bg-background">
                        <p className="text-[10px] font-bold uppercase tracking-[0.15em] text-muted-foreground">Risk per trade</p>
                        <p className="text-2xl font-black font-mono text-card-foreground mt-1">
                          ${calc.riskDollars.toFixed(2)}
                        </p>
                        <p className="text-xs text-muted-foreground">{calc.riskPercent.toFixed(1)}% of balance</p>
                      </div>
                      <div className="p-4 rounded-xl bg-background">
                        <p className="text-[10px] font-bold uppercase tracking-[0.15em] text-muted-foreground">Position size</p>
                        <p className="text-2xl font-black font-mono text-card-foreground mt-1">
                          {calc.positionSize.toFixed(4)}
                        </p>
                        <p className="text-xs text-muted-foreground">{activeAsset === 'gold' ? 'troy oz' : 'troy oz'}</p>
                      </div>
                      <div className="p-4 rounded-xl bg-background">
                        <p className="text-[10px] font-bold uppercase tracking-[0.15em] text-muted-foreground">Lot size</p>
                        <p className="text-2xl font-black font-mono text-card-foreground mt-1">
                          {calc.lotSize.toFixed(4)}
                        </p>
                        <p className="text-xs text-muted-foreground">standard lots</p>
                      </div>
                      <div className="p-4 rounded-xl bg-background">
                        <p className="text-[10px] font-bold uppercase tracking-[0.15em] text-muted-foreground">Risk / Reward</p>
                        <p className={cn("text-2xl font-black font-mono mt-1", calc.riskReward >= 2 ? "text-emerald-400" : calc.riskReward >= 1.5 ? "text-amber-400" : "text-red-400")}>
                          1 : {calc.riskReward.toFixed(1)}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {calc.riskReward >= 2 ? 'Excellent' : calc.riskReward >= 1.5 ? 'Acceptable' : 'Poor'}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Entry / SL / TP */}
                <Card className="bg-card border-border">
                  <CardHeader className="pb-4">
                    <CardTitle className="text-sm font-bold text-card-foreground">Price levels</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                        <div className="flex items-center gap-2">
                          <TrendingUp className="w-4 h-4 text-emerald-500" />
                          <span className="text-sm font-bold text-card-foreground">Take profit</span>
                        </div>
                        <span className="font-mono font-bold text-emerald-400">
                          ${calc.takeProfitPrice.toFixed(2)}
                        </span>
                      </div>
                      <div className="flex items-center justify-between p-3 rounded-lg bg-background border border-border">
                        <div className="flex items-center gap-2">
                          <DollarSign className="w-4 h-4 text-muted-foreground" />
                          <span className="text-sm font-bold text-card-foreground">Entry price</span>
                        </div>
                        <span className="font-mono font-bold text-card-foreground">
                          ${livePrice?.toFixed(2)}
                        </span>
                      </div>
                      <div className="flex items-center justify-between p-3 rounded-lg bg-red-500/10 border border-red-500/20">
                        <div className="flex items-center gap-2">
                          <TrendingDown className="w-4 h-4 text-red-500" />
                          <span className="text-sm font-bold text-card-foreground">Stop loss</span>
                        </div>
                        <span className="font-mono font-bold text-red-400">
                          ${calc.stopLossPrice.toFixed(2)}
                        </span>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Quick Summary */}
                <Card className="bg-gradient-to-br from-emerald-500/10 to-emerald-500/5 border-emerald-500/20">
                  <CardContent className="pt-6">
                    <div className="flex items-center gap-2 mb-3">
                      <Shield className="w-5 h-5 text-emerald-500" />
                      <span className="text-sm font-bold text-card-foreground">Trade summary</span>
                    </div>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <p className="text-muted-foreground">You risk</p>
                        <p className="font-bold text-card-foreground">${calc.riskDollars.toFixed(2)} ({calc.riskPercent.toFixed(1)}%)</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Position</p>
                        <p className="font-bold text-card-foreground">{calc.positionSize.toFixed(4)} oz</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">If TP hits</p>
                        <p className="font-bold text-emerald-400">+${(calc.riskDollars * calc.riskReward).toFixed(2)}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">If SL hits</p>
                        <p className="font-bold text-red-400">-${calc.riskDollars.toFixed(2)}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </>
            ) : (
              <Card className="bg-card border-border">
                <CardContent className="pt-6">
                  <p className="text-muted-foreground text-center">
                    {isLoading ? 'Loading price data...' : 'Enter a valid balance to calculate position size.'}
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
