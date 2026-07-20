'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { apiClient } from '@/lib/api-client';
import { AssetType, PredictionItem, WatchlistItem, WatchlistSymbol } from '@/lib/api-types';
import { TerminalButton } from '@/components/Common/TerminalCard';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { AlertTriangle, Eye, Plus, Sparkles, Trash2, RefreshCcw } from 'lucide-react';

function symbolToAssetType(symbol: string): AssetType {
  if (symbol.includes('XAG')) return 'silver';
  return 'gold';
}

export default function WatchlistTable() {
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [symbols, setSymbols] = useState<WatchlistSymbol[]>([]);
  const [selectedSymbol, setSelectedSymbol] = useState('');
  const [alertThreshold, setAlertThreshold] = useState('');
  const [notes, setNotes] = useState('');
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [operationMessage, setOperationMessage] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [hoveredItem, setHoveredItem] = useState<WatchlistItem | null>(null);
  const [predictionState, setPredictionState] = useState<Record<string, PredictionItem>>({});

  // Stable refs for interval callbacks — avoids re-render loops
  const watchlistRef = useRef(watchlist);
  watchlistRef.current = watchlist;
  const predictionStateRef = useRef(predictionState);
  predictionStateRef.current = predictionState;

  const selectedSymbolMeta = useMemo(
    () => symbols.find((item) => item.symbol === selectedSymbol),
    [selectedSymbol, symbols]
  );

  const fetchSymbols = useCallback(async () => {
    try {
      const data = await apiClient.getWatchlistSymbols();
      setSymbols(data?.symbols ?? []);
      if (!selectedSymbol && data?.symbols?.length) {
        setSelectedSymbol(data.symbols[0].symbol);
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Unable to load symbol catalog.';
      setError(message);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchWatchlist = useCallback(async () => {
    setError(null);
    try {
      const data = await apiClient.getWatchlist();
      setWatchlist(data?.watchlist ?? []);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Unable to load watchlist.';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchPreview = useCallback(async (symbol: string) => {
    const asset = symbolToAssetType(symbol);
    const response = await apiClient.getLatestPrediction(asset);
    const prediction = response?.predictions?.[0];
    if (prediction) {
      setPredictionState((prev) => ({ ...prev, [symbol]: prediction }));
    }
    return prediction;
  }, []);

  const refreshPrices = useCallback(async () => {
    const currentWatchlist = watchlistRef.current;
    const currentPredictions = predictionStateRef.current;
    if (!currentWatchlist.length) return;
    setRefreshing(true);
    try {
      await Promise.all(
        currentWatchlist.map(async (item) => {
          if (!currentPredictions[item.symbol]) {
            const asset = symbolToAssetType(item.symbol);
            const response = await apiClient.getLatestPrediction(asset);
            const prediction = response?.predictions?.[0];
            if (prediction) {
              setPredictionState((prev) => ({ ...prev, [item.symbol]: prediction }));
            }
          }
        })
      );
    } finally {
      setRefreshing(false);
    }
  }, []);

  // Initial load only — runs once
  useEffect(() => {
    const init = async () => {
      await fetchSymbols();
      await fetchWatchlist();
    };
    init();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Periodic refresh — stable, no dependency churn
  useEffect(() => {
    const interval = setInterval(() => {
      fetchWatchlist();
      refreshPrices();
    }, 20000);
    return () => clearInterval(interval);
  }, [fetchWatchlist, refreshPrices]);

  // Hover preview — load on demand
  useEffect(() => {
    if (hoveredItem && !predictionState[hoveredItem.symbol]) {
      fetchPreview(hoveredItem.symbol);
    }
  }, [hoveredItem, predictionState, fetchPreview]);

  async function handleAddItem() {
    if (!selectedSymbol) {
      setError('Please choose a symbol to add.');
      return;
    }
    setError(null);
    try {
      const payload = {
        symbol: selectedSymbol,
        display_name: selectedSymbolMeta?.display_name || selectedSymbol,
        notifications_enabled: notificationsEnabled,
        alert_threshold: alertThreshold ? Number(alertThreshold) : null,
        notes: notes || undefined,
      };
      const response = await apiClient.addWatchlistItem(payload);
      setWatchlist((previous) => [...previous, response.item]);
      setOperationMessage(`${response.item.display_name} added to your watchlist.`);
      setNotes('');
      setAlertThreshold('');
      setNotificationsEnabled(true);
      fetchPreview(response.item.symbol);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Unable to add asset to watchlist.';
      setError(message);
    }
  }

  async function handleRemoveItem(itemId: number) {
    setError(null);
    try {
      await apiClient.removeWatchlistItem(itemId);
      setWatchlist((prev) => prev.filter((item) => item.id !== itemId));
      setOperationMessage('Watchlist item removed successfully.');
      setPredictionState((prev) => {
        const next = { ...prev };
        const removed = watchlist.find((item) => item.id === itemId);
        if (removed) delete next[removed.symbol];
        return next;
      });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'An error occurred';
      setError(message);
    }
  }

  const preview = hoveredItem ? predictionState[hoveredItem.symbol] : undefined;

  return (
    <div className="space-y-6">
      {/* Add new asset form */}
      <div className="border border-terminal-rule bg-terminal-panel p-6">
        <div className="mb-5 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-sm font-mono font-black text-terminal-value tracking-wider">ADD NEW ASSET</h2>
            <p className="text-[10px] font-mono text-terminal-label mt-1">Select a symbol and configure alerts for your watchlist.</p>
          </div>
          <TerminalButton variant="secondary" size="sm" onClick={fetchWatchlist}>
            <RefreshCcw className="w-3 h-3" /> REFRESH
          </TerminalButton>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label className="text-[9px] font-mono font-bold uppercase tracking-widest text-terminal-label">Symbol</Label>
            <select
              value={selectedSymbol}
              onChange={(event) => setSelectedSymbol(event.target.value)}
              className="h-10 w-full border border-terminal-rule bg-terminal-panel px-3 text-xs font-mono text-terminal-value outline-none focus:border-terminal-hold"
            >
              {symbols.map((symbol) => (
                <option key={symbol.symbol} value={symbol.symbol}>
                  {symbol.display_name} ({symbol.symbol})
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <Label className="text-[9px] font-mono font-bold uppercase tracking-widest text-terminal-label">Alert Threshold</Label>
            <Input
              type="number"
              min="0"
              step="0.01"
              value={alertThreshold}
              onChange={(event) => setAlertThreshold(event.target.value)}
              placeholder="e.g. 2100"
              className="bg-terminal-panel border-terminal-rule text-terminal-value font-mono text-xs rounded-none focus:border-terminal-hold"
            />
          </div>

          <div className="space-y-2 sm:col-span-2">
            <Label className="text-[9px] font-mono font-bold uppercase tracking-widest text-terminal-label">Notes</Label>
            <Textarea
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              placeholder="Add a quick reminder or trade thesis."
              rows={3}
              className="bg-terminal-panel border-terminal-rule text-terminal-value font-mono text-xs rounded-none focus:border-terminal-hold"
            />
          </div>

          <div className="flex items-center gap-3 sm:col-span-2">
            <label className="inline-flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={notificationsEnabled}
                onChange={(event) => setNotificationsEnabled(event.target.checked)}
                className="accent-terminal-hold"
              />
              <span className="text-[10px] font-mono font-bold text-terminal-value">Enable alert notifications</span>
            </label>
          </div>
        </div>

        <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:justify-between sm:items-center">
          <div>
            <p className="text-[9px] font-mono font-bold uppercase tracking-widest text-terminal-label">Selected</p>
            <p className="text-xs font-mono text-terminal-value">{selectedSymbolMeta?.display_name ?? selectedSymbol}</p>
          </div>
          <TerminalButton variant="primary" size="sm" onClick={handleAddItem}>
            <Plus className="w-3.5 h-3.5" /> ADD TO WATCHLIST
          </TerminalButton>
        </div>

        {operationMessage && (
          <div className="mt-4 border border-terminal-buy/20 bg-terminal-buy/5 px-3 py-2">
            <p className="text-[10px] font-mono text-terminal-buy">{operationMessage}</p>
          </div>
        )}
        {error && (
          <div className="mt-4 border border-terminal-sell/20 bg-terminal-sell/5 px-3 py-2">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-3.5 h-3.5 text-terminal-sell" />
              <span className="text-[10px] font-mono text-terminal-sell">{error}</span>
            </div>
          </div>
        )}
      </div>

      {/* Watchlist table + Preview */}
      <div className="grid grid-cols-1 xl:grid-cols-[1.4fr_0.95fr] gap-6">
        {/* Table */}
        <div className="border border-terminal-rule bg-terminal-panel p-6">
          <div className="mb-5 flex items-center justify-between gap-4">
            <div>
              <h2 className="text-sm font-mono font-black text-terminal-value tracking-wider">WATCHLIST</h2>
              <p className="text-[10px] font-mono text-terminal-label mt-1">Hover a row to preview signal details.</p>
            </div>
            <span className="border border-terminal-rule px-3 py-1 text-[9px] font-mono font-bold text-terminal-label tracking-widest uppercase">
              {watchlist.length} ITEMS
            </span>
          </div>

          <div className="overflow-hidden border border-terminal-rule">
            <table className="min-w-full border-collapse text-left">
              <thead className="bg-terminal-panel">
                <tr className="border-b border-terminal-rule">
                  <th className="px-4 py-3 text-[9px] font-mono font-bold uppercase tracking-widest text-terminal-label">Symbol</th>
                  <th className="px-4 py-3 text-[9px] font-mono font-bold uppercase tracking-widest text-terminal-label">Signal</th>
                  <th className="px-4 py-3 text-[9px] font-mono font-bold uppercase tracking-widest text-terminal-label">Price</th>
                  <th className="px-4 py-3 text-[9px] font-mono font-bold uppercase tracking-widest text-terminal-label">Alerts</th>
                  <th className="px-4 py-3 text-[9px] font-mono font-bold uppercase tracking-widest text-terminal-label">Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={5} className="px-4 py-8 text-center text-[10px] font-mono text-terminal-label">
                      Loading watchlist...
                    </td>
                  </tr>
                ) : watchlist.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-4 py-8 text-center text-[10px] font-mono text-terminal-label">
                      Your watchlist is empty. Add a symbol to get started.
                    </td>
                  </tr>
                ) : (
                  watchlist.map((item) => {
                    const previewItem = predictionState[item.symbol];
                    const signalText = previewItem?.signal ?? '—';
                    const signalClass =
                      signalText === 'BUY' ? 'text-terminal-buy border-terminal-buy/20 bg-terminal-buy/5' :
                      signalText === 'SELL' ? 'text-terminal-sell border-terminal-sell/20 bg-terminal-sell/5' :
                      'text-terminal-hold border-terminal-hold/20 bg-terminal-hold/5';
                    return (
                      <tr
                        key={item.id}
                        onMouseEnter={() => setHoveredItem(item)}
                        className="border-b border-terminal-rule hover:bg-terminal-hold/5 transition-colors"
                      >
                        <td className="px-4 py-3">
                          <div className="text-xs font-mono font-bold text-terminal-value">{item.display_name || item.symbol}</div>
                          <div className="text-[9px] font-mono text-terminal-label">{item.symbol}</div>
                        </td>
                        <td className="px-4 py-3">
                          <span className={`inline-block border px-2 py-0.5 text-[9px] font-mono font-bold uppercase tracking-widest ${signalClass}`}>
                            {signalText}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-xs font-mono font-bold text-terminal-value tabular-nums">
                          {previewItem ? `$${previewItem.price.toFixed(2)}` : '—'}
                        </td>
                        <td className="px-4 py-3 text-[10px] font-mono text-terminal-label">
                          {item.alert_threshold ? `$${item.alert_threshold.toFixed(2)}` : 'Off'}
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex gap-1.5">
                            <TerminalButton variant="secondary" size="sm" onClick={() => fetchPreview(item.symbol)}>
                              <Eye className="w-3 h-3" />
                            </TerminalButton>
                            <TerminalButton variant="danger" size="sm" onClick={() => handleRemoveItem(item.id)}>
                              <Trash2 className="w-3 h-3" />
                            </TerminalButton>
                          </div>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Preview panel */}
        <div className="border border-terminal-rule bg-terminal-panel p-6">
          <div className="flex items-center justify-between gap-4 mb-5">
            <div>
              <h2 className="text-sm font-mono font-black text-terminal-value tracking-wider">PREVIEW</h2>
              <p className="text-[10px] font-mono text-terminal-label mt-1">Hover a row to see prediction details.</p>
            </div>
            <div className="flex items-center gap-1.5 border border-terminal-rule px-3 py-1">
              <Sparkles className="w-3 h-3 text-terminal-hold" />
              <span className="text-[8px] font-mono font-bold text-terminal-label tracking-widest uppercase">Live Insights</span>
            </div>
          </div>

          <div className="border border-terminal-rule p-5 min-h-[280px]">
            {hoveredItem ? (
              <div className="space-y-4">
                <div className="grid gap-3 sm:grid-cols-2">
                  <div>
                    <p className="text-[8px] font-mono font-bold uppercase tracking-widest text-terminal-label">Symbol</p>
                    <p className="text-sm font-mono font-bold text-terminal-value">{hoveredItem.display_name || hoveredItem.symbol}</p>
                    <p className="text-[10px] font-mono text-terminal-label">{hoveredItem.symbol}</p>
                  </div>
                  <div>
                    <p className="text-[8px] font-mono font-bold uppercase tracking-widest text-terminal-label">Alerts</p>
                    <p className="text-sm font-mono font-bold text-terminal-value">{hoveredItem.alert_threshold ? `$${hoveredItem.alert_threshold.toFixed(2)}` : 'Disabled'}</p>
                    <p className="text-[10px] font-mono text-terminal-label">{hoveredItem.notifications_enabled ? 'Notifications on' : 'Notifications off'}</p>
                  </div>
                </div>

                <div className="grid gap-2 grid-cols-3">
                  <div className="border border-terminal-rule bg-terminal-panel p-3">
                    <p className="text-[8px] font-mono font-bold uppercase tracking-widest text-terminal-label">Signal</p>
                    <p className="mt-1 text-lg font-black font-mono text-terminal-value">{preview?.signal ?? '—'}</p>
                  </div>
                  <div className="border border-terminal-rule bg-terminal-panel p-3">
                    <p className="text-[8px] font-mono font-bold uppercase tracking-widest text-terminal-label">Price</p>
                    <p className="mt-1 text-lg font-black font-mono text-terminal-value tabular-nums">{preview ? `$${preview.price.toFixed(2)}` : '—'}</p>
                  </div>
                  <div className="border border-terminal-rule bg-terminal-panel p-3">
                    <p className="text-[8px] font-mono font-bold uppercase tracking-widest text-terminal-label">Confidence</p>
                    <p className="mt-1 text-lg font-black font-mono text-terminal-value">{preview?.confidence != null ? `${Math.round(preview.confidence * 100)}%` : '—'}</p>
                  </div>
                </div>

                <div className="border border-terminal-rule p-4">
                  <div className="mb-3 flex items-center justify-between gap-3">
                    <p className="text-[8px] font-mono font-bold uppercase tracking-widest text-terminal-label">Mini Trend</p>
                    <span className="text-[8px] font-mono text-terminal-label">
                      {preview ? preview.timestamp?.split('T')[1]?.slice(0, 8) : '—'}
                    </span>
                  </div>
                  <div className="flex h-24 items-end gap-1">
                    {preview ? (
                      Array.from({ length: 7 }, (_, i) => {
                        const base = preview.confidence * 100;
                        const variance = Math.sin(i * 1.3 + base) * 20;
                        const height = Math.max(15, Math.min(95, base + variance));
                        const isLast = i === 6;
                        return (
                          <div
                            key={i}
                            style={{ height: `${height}%` }}
                            className={`w-full ${isLast ? 'bg-terminal-hold' : 'bg-terminal-hold/30'}`}
                          />
                        );
                      })
                    ) : (
                      <p className="text-[10px] font-mono text-terminal-label w-full text-center self-center">No data available</p>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center h-full min-h-[240px] text-center">
                <div>
                  <p className="text-xs font-mono text-terminal-label">Hover over any watchlist row</p>
                  <p className="text-[10px] font-mono text-terminal-label mt-1">to preview the latest signal and price.</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
