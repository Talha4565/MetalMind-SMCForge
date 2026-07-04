/**
 * API Type Definitions
 * Based on the MetalMind SMCForge Architecture
 */

// --- Auth Types ---

export interface User {
  id: string;
  email: string;
  username: string;
  verified: boolean;
  createdAt?: string;
  lastLogin?: string;
}

export interface Profile {
  id: string;
  email: string;
  name: string;
  username: string;
  is_active: boolean;
  is_verified: boolean;
  totp_enabled: boolean;
  created_at?: string;
  last_login?: string;
  settings?: {
    avatar_url?: string;
    notifications?: boolean;
    theme?: string;
  };
}

export interface AuthResponse {
  success: boolean;
  message: string;
  token: string;
  refresh_token: string;
  data: {
    user: User;
    tokens: {
      accessToken: string;
      refreshToken: string;
    };
  };
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload extends LoginPayload {
  confirmPassword?: string;
}

// --- Prediction & Signal Types ---

export type AssetType = 'gold' | 'silver';
export type SignalAction = 'BUY' | 'SELL' | 'HOLD' | number;

export interface SHAPValue {
  feature: string;
  contribution: number;
}

export interface PredictionItem {
  asset: string;
  signal: SignalAction;
  confidence: number;
  probability: number;
  price: number;
  open?: number;
  high?: number;
  low?: number;
  close?: number;
  timestamp: string;
  shap_values: SHAPValue[];
}

export interface PredictionResponse {
  asset: AssetType;
  predictions: PredictionItem[];
  total_signals: number;
  data_range?: {
    start: string;
    end: string;
  };
}

// --- Backtest Types ---

export interface BacktestRequest {
  asset: AssetType;
  start_date: string; // ISO format
  end_date: string;   // ISO format
  strategy: string;
  initial_capital?: number;
}

export interface Trade {
  id: string;
  asset: AssetType;
  type: 'BUY' | 'SELL';
  entry_price: number;
  exit_price: number;
  entry_time: string;
  exit_time: string;
  profit: number;
  profit_percentage: number;
}

export interface BacktestResponse {
  win_rate: number;
  profit_factor: number;
  max_drawdown: number;
  total_trades: number;
  net_profit: number;
  trades: Trade[];
}

export interface WatchlistItem {
  id: number;
  symbol: string;
  display_name: string;
  notifications_enabled: boolean;
  alert_threshold?: number | null;
  notes?: string | null;
  order: number;
  created_at?: string;
}

export interface WatchlistSymbol {
  symbol: string;
  display_name: string;
  asset_type: string;
}

export interface WatchlistResponse {
  watchlist: WatchlistItem[];
  count: number;
}

export interface SymbolsResponse {
  symbols: WatchlistSymbol[];
}

// --- Prediction History Types ---

export interface PredictionLogItem {
  timestamp: string;
  asset: string;
  signal: number;
  signal_text: string;
  confidence: number;
  price: number;
  tp_price: number | null;
  sl_price: number | null;
  shap_values: SHAPValue[];
  model_version: string;
  actual_outcome: string | null;
  actual_pnl: number | null;
  outcome_checked_at: string | null;
}

export interface PredictionHistorySummary {
  total_predictions: number;
  buy_signals: number;
  sell_signals: number;
  hold_signals: number;
  evaluated: number;
  wins: number;
  losses: number;
  avg_confidence: number;
}

export interface PredictionHistoryResponse {
  predictions: PredictionLogItem[];
  summary: PredictionHistorySummary;
}

// --- Error Types ---

export interface ApiError {
  error: string;
  details?: string;
  status: number;
  timestamp: string;
}
