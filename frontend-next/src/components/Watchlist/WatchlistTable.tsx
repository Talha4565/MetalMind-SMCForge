'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { apiClient } from '@/lib/api-client';
import { AssetType, PredictionItem, WatchlistItem, WatchlistSymbol } from '@/lib/api-types';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { AlertTriangle, Eye, Plus, Sparkles, Trash2 } from 'lucide-react';

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

  const selectedSymbolMeta = useMemo(
    () => symbols.find((item) => item.symbol === selectedSymbol),
    [selectedSymbol, symbols]
  );

  const fetchSymbols = useCallback(async () => {
    try {
      const data = await apiClient.getWatchlistSymbols();
      setSymbols(data.symbols);
      if (!selectedSymbol && data.symbols.length) {
        setSelectedSymbol(data.symbols[0].symbol);
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Unable to load symbol catalog.';
      setError(message);
    }
  }, [selectedSymbol]);

  const fetchWatchlist = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.getWatchlist();
      setWatchlist(data.watchlist);
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
    if (!watchlist.length) return;
    setRefreshing(true);
    try {
      await Promise.all(
        watchlist.map(async (item) => {
          if (!predictionState[item.symbol]) {
            await fetchPreview(item.symbol);
          }
        })
      );
    } finally {
      setRefreshing(false);
    }
  }, [watchlist, predictionState, fetchPreview]);

  useEffect(() => {
    const initialize = async () => {
      await fetchSymbols();
      await fetchWatchlist();
    };
    
    initialize();

    const interval = window.setInterval(() => {
      fetchWatchlist();
      refreshPrices();
    }, 20000);

    return () => window.clearInterval(interval);
  }, [fetchSymbols, fetchWatchlist, refreshPrices]);

  useEffect(() => {
    if (hoveredItem && !predictionState[hoveredItem.symbol]) {
      const loadPreview = async () => {
        try {
          await fetchPreview(hoveredItem.symbol);
        } catch {
          // Error handled in fetchPreview
        }
      };
      loadPreview();
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
      fetchPreview(response.item.symbol).catch(() => {});
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
        if (removed) {
          delete next[removed.symbol];
        }
        return next;
      });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'An error occurred';
      setError(message);
    }
  }

  const preview = hoveredItem ? predictionState[hoveredItem.symbol] : undefined;

  return (
    <div className="space-y-8">
      <div className="rounded-3xl border border-border bg-card p-6 shadow-lg shadow-black/20">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-slate-500">Watchlist</p>
            <h1 className="text-3xl font-black text-card-foreground">Trade-ready watchlist</h1>
            <p className="max-w-2xl mt-2 text-sm leading-6 text-muted-foreground">
              Keep a curated set of precious metals symbols in one place, view live prediction signals, and configure alert thresholds.
            </p>
          </div>
          <div className="rounded-3xl border border-border bg-background p-4 shadow-inner shadow-white/5">
            <div className="text-xs uppercase tracking-[0.3em] text-slate-500">Live refresh</div>
            <div className="mt-2 text-2xl font-black text-card-foreground">{refreshing ? 'Updatingâ€¦' : 'Every 20s'}</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-[1.4fr_0.95fr] gap-6">
        <section className="space-y-6">
          <div className="rounded-3xl border border-border bg-card p-6">
            <div className="mb-5 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <h2 className="text-xl font-semibold text-card-foreground">Add new asset</h2>
                <p className="text-sm text-slate-500">Select a symbol and configure alerts for your next trade watchlist.</p>
              </div>
              <Button variant="secondary" onClick={fetchWatchlist}>Refresh list</Button>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="symbol">Symbol</Label>
                <select
                  id="symbol"
                  value={selectedSymbol}
                  onChange={(event) => setSelectedSymbol(event.target.value)}
                  className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm text-card-foreground outline-none transition focus:border-blue-500"
                >
                  {symbols.map((symbol) => (
                    <option key={symbol.symbol} value={symbol.symbol} className="bg-background text-card-foreground">
                      {symbol.display_name} ({symbol.symbol})
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="alertThreshold">Alert threshold</Label>
                <Input
                  id="alertThreshold"
                  type="number"
                  min="0"
                  step="0.01"
                  value={alertThreshold}
                  onChange={(event) => setAlertThreshold(event.target.value)}
                  placeholder="e.g. 2100"
                />
              </div>

              <div className="space-y-2 sm:col-span-2">
                <Label htmlFor="notes">Notes</Label>
                <Textarea
                  id="notes"
                  value={notes}
                  onChange={(event) => setNotes(event.target.value)}
                  placeholder="Add a quick reminder or trade thesis."
                  rows={3}
                />
              </div>

              <div className="flex items-center gap-3 sm:col-span-2">
                <label className="inline-flex items-center gap-2 cursor-pointer text-sm text-secondary-foreground">
                  <input
                    type="checkbox"
                    checked={notificationsEnabled}
                    onChange={(event) => setNotificationsEnabled(event.target.checked)}
                    className="h-4 w-4 rounded border-border bg-secondary text-blue-500 focus:ring-blue-500"
                  />
                  Enable alert notifications
                </label>
              </div>
            </div>

            <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:justify-between sm:items-center">
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Next symbol</p>
                <p className="text-card-foreground">{selectedSymbolMeta?.display_name ?? selectedSymbol}</p>
              </div>
              <Button onClick={handleAddItem} className="w-full sm:w-auto">
                <Plus className="mr-2 h-4 w-4" /> Add to watchlist
              </Button>
            </div>

            {operationMessage ? (
              <div className="mt-4 rounded-2xl border border-emerald-500/20 bg-emerald-500/10 p-4 text-sm text-emerald-200">
                {operationMessage}
              </div>
            ) : null}

            {error ? (
              <div className="mt-4 rounded-2xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-200">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4" />
                  <span>{error}</span>
                </div>
              </div>
            ) : null}
          </div>

          <div className="rounded-3xl border border-border bg-card p-6">
            <div className="mb-5 flex items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-semibold text-card-foreground">Watchlist</h2>
                <p className="text-sm text-slate-500">Tap a row to preview current signal details.</p>
              </div>
              <span className="rounded-full bg-secondary px-3 py-1 text-xs uppercase tracking-[0.25em] text-muted-foreground">
                {watchlist.length} items
              </span>
            </div>

            <div className="overflow-hidden rounded-3xl border border-border bg-background">
              <table className="min-w-full border-collapse text-left text-sm">
                <thead className="bg-card text-muted-foreground">
                  <tr>
                    <th className="px-4 py-4">Symbol</th>
                    <th className="px-4 py-4">Signal</th>
                    <th className="px-4 py-4">Price</th>
                    <th className="px-4 py-4">Alerts</th>
                    <th className="px-4 py-4">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <tr>
                      <td colSpan={5} className="px-4 py-8 text-center text-slate-500">Loading watchlistâ€¦</td>
                    </tr>
                  ) : watchlist.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="px-4 py-8 text-center text-slate-500">Your watchlist is empty. Add a symbol to get started.</td>
                    </tr>
                  ) : (
                    watchlist.map((item) => {
                      const previewItem = predictionState[item.symbol];
                      return (
                        <tr
                          key={item.id}
                          onMouseEnter={() => setHoveredItem(item)}
                          onMouseLeave={() => setHoveredItem(null)}
                          className="border-t border-border hover:bg-card"
                        >
                          <td className="px-4 py-4">
                            <div className="font-semibold text-card-foreground">{item.display_name || item.symbol}</div>
                            <div className="text-xs text-slate-500">{item.symbol}</div>
                          </td>
                          <td className="px-4 py-4">
                            <span className="inline-flex rounded-full bg-secondary px-3 py-1 text-xs font-semibold uppercase tracking-[0.24em] text-secondary-foreground">
                              {previewItem?.signal ?? 'Waiting'}
                            </span>
                          </td>
                          <td className="px-4 py-4 text-foreground">
                            {previewItem ? `$${previewItem.price.toFixed(2)}` : 'â€”'}
                          </td>
                          <td className="px-4 py-4 text-secondary-foreground">
                            {item.alert_threshold ? `@$${item.alert_threshold.toFixed(2)}` : 'Off'}
                          </td>
                          <td className="px-4 py-4">
                            <div className="flex flex-wrap gap-2">
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => fetchPreview(item.symbol)}
                                className="gap-2"
                              >
                                <Eye className="h-4 w-4" /> Preview
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleRemoveItem(item.id)}
                                className="gap-2 text-rose-300 hover:text-rose-100"
                              >
                                <Trash2 className="h-4 w-4" /> Remove
                              </Button>
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
        </section>

        <section className="space-y-6">
          <div className="rounded-3xl border border-border bg-card p-6">
            <div className="flex items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-semibold text-card-foreground">Hover preview</h2>
                <p className="text-sm text-slate-500">Current prediction details for the selected watchlist asset.</p>
              </div>
              <div className="inline-flex items-center gap-2 rounded-full bg-background px-3 py-1 text-xs uppercase tracking-[0.24em] text-muted-foreground">
                <Sparkles className="h-4 w-4" /> Live insights
              </div>
            </div>

            <div className="mt-6 rounded-3xl border border-border bg-background p-5">
              {hoveredItem ? (
                <div className="space-y-4">
                  <div className="grid gap-3 sm:grid-cols-2">
                    <div>
                      <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Symbol</p>
                      <p className="text-lg font-semibold text-card-foreground">{hoveredItem.display_name || hoveredItem.symbol}</p>
                      <p className="text-sm text-slate-500">{hoveredItem.symbol}</p>
                    </div>
                    <div>
                      <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Alerts</p>
                      <p className="text-lg font-semibold text-card-foreground">{hoveredItem.alert_threshold ? `$${hoveredItem.alert_threshold.toFixed(2)}` : 'Disabled'}</p>
                      <p className="text-sm text-slate-500">{hoveredItem.notifications_enabled ? 'Notifications on' : 'Notifications off'}</p>
                    </div>
                  </div>

                  <div className="grid gap-3 sm:grid-cols-3">
                    <div className="rounded-3xl bg-card p-4">
                      <span className="text-xs uppercase tracking-[0.24em] text-slate-500">Signal</span>
                      <p className="mt-2 text-2xl font-black text-card-foreground">{preview?.signal ?? 'Loadingâ€¦'}</p>
                    </div>
                    <div className="rounded-3xl bg-card p-4">
                      <span className="text-xs uppercase tracking-[0.24em] text-slate-500">Price</span>
                      <p className="mt-2 text-2xl font-black text-card-foreground">{preview ? `$${preview.price.toFixed(2)}` : 'â€”'}</p>
                    </div>
                    <div className="rounded-3xl bg-card p-4">
                      <span className="text-xs uppercase tracking-[0.24em] text-slate-500">Confidence</span>
                      <p className="mt-2 text-2xl font-black text-card-foreground">{preview ? `${Math.round(preview.confidence)}%` : 'â€”'}</p>
                    </div>
                  </div>

                  <div className="relative overflow-hidden rounded-[1.75rem] border border-border bg-background p-4">
                    <div className="mb-3 flex items-center justify-between gap-3">
                      <div>
                        <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Mini trend</p>
                        <p className="text-sm text-muted-foreground">Estimated signal preview</p>
                      </div>
                      <span className="rounded-full bg-secondary px-3 py-1 text-[11px] uppercase tracking-[0.25em] text-muted-foreground">
                        {preview ? preview.timestamp.split('T')[1]?.slice(0, 8) : 'Waiting'}
                      </span>
                    </div>
                    <div className="flex h-28 items-end gap-1">
                      {[40, 60, 30, 70, 55, 85, 50].map((height, index) => (
                        <div
                          key={index}
                          style={{ height: `${height / 1.2}%` }}
                          className="w-full rounded-full bg-gradient-to-t from-blue-500 via-sky-400 to-cyan-300"
                        />
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="space-y-4 text-slate-500">
                  <p className="text-sm">Hover over any watchlist row to preview the latest symbol signal and price.</p>
                  <p className="text-xs uppercase tracking-[0.25em] text-muted-foreground">Ready when you are</p>
                </div>
              )}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
