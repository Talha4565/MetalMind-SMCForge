import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import type { Prediction, AssetType, WatchlistItem } from '@/types';

interface TradingState {
  // Predictions
  latestPrediction: Prediction | null;
  predictionHistory: Prediction[];
  
  // Selected asset
  selectedAsset: AssetType;
  
  // Watchlist
  watchlist: WatchlistItem[];
  
  // UI state
  isLoading: boolean;
  error: string | null;
  
  // Real-time connection
  isConnected: boolean;
  lastUpdate: string | null;
}

interface TradingActions {
  // Predictions
  setPrediction: (prediction: Prediction) => void;
  addPredictionToHistory: (prediction: Prediction) => void;
  clearPredictionHistory: () => void;
  
  // Asset selection
  setSelectedAsset: (asset: AssetType) => void;
  
  // Watchlist
  setWatchlist: (watchlist: WatchlistItem[]) => void;
  addToWatchlist: (item: WatchlistItem) => void;
  removeFromWatchlist: (id: string) => void;
  updateWatchlistItem: (id: string, updates: Partial<WatchlistItem>) => void;
  
  // UI state
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
  
  // Connection state
  setConnected: (connected: boolean) => void;
  updateLastUpdate: () => void;
}

type TradingStore = TradingState & TradingActions;

/**
 * Trading Store
 * Manages trading signals, predictions, and watchlist
 */
export const useTradingStore = create<TradingStore>()(
  immer((set) => ({
    // Initial State
    latestPrediction: null,
    predictionHistory: [],
    selectedAsset: 'XAUUSD',
    watchlist: [],
    isLoading: false,
    error: null,
    isConnected: false,
    lastUpdate: null,

    // Prediction Actions
    setPrediction: (prediction) =>
      set((state) => {
        state.latestPrediction = prediction;
        state.lastUpdate = new Date().toISOString();
      }),

    addPredictionToHistory: (prediction) =>
      set((state) => {
        // Add to beginning of array
        state.predictionHistory.unshift(prediction);
        
        // Keep only last 100 predictions
        if (state.predictionHistory.length > 100) {
          state.predictionHistory = state.predictionHistory.slice(0, 100);
        }
      }),

    clearPredictionHistory: () =>
      set((state) => {
        state.predictionHistory = [];
      }),

    // Asset Actions
    setSelectedAsset: (asset) =>
      set((state) => {
        state.selectedAsset = asset;
        // Clear prediction when switching assets
        state.latestPrediction = null;
      }),

    // Watchlist Actions
    setWatchlist: (watchlist) =>
      set((state) => {
        state.watchlist = watchlist;
      }),

    addToWatchlist: (item) =>
      set((state) => {
        // Check if already exists
        const exists = state.watchlist.some((w) => w.asset === item.asset);
        if (!exists) {
          state.watchlist.push(item);
        }
      }),

    removeFromWatchlist: (id) =>
      set((state) => {
        state.watchlist = state.watchlist.filter((item) => item.id !== id);
      }),

    updateWatchlistItem: (id, updates) =>
      set((state) => {
        const index = state.watchlist.findIndex((item) => item.id === id);
        if (index !== -1) {
          state.watchlist[index] = { ...state.watchlist[index], ...updates };
        }
      }),

    // UI State Actions
    setLoading: (loading) =>
      set((state) => {
        state.isLoading = loading;
      }),

    setError: (error) =>
      set((state) => {
        state.error = error;
      }),

    clearError: () =>
      set((state) => {
        state.error = null;
      }),

    // Connection Actions
    setConnected: (connected) =>
      set((state) => {
        state.isConnected = connected;
      }),

    updateLastUpdate: () =>
      set((state) => {
        state.lastUpdate = new Date().toISOString();
      }),
  }))
);
