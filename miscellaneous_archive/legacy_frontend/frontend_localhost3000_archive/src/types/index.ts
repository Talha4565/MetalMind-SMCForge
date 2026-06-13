// Global Type Definitions

export interface User {
  id: string;
  email: string;
  username: string;
  verified: boolean;
  createdAt: string;
  lastLogin?: string;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
  rememberMe?: boolean;
}

export interface RegisterData {
  email: string;
  username: string;
  password: string;
  confirmPassword: string;
}

export interface OTPVerification {
  email: string;
  otp: string;
}

export type SignalType = 'BUY' | 'SELL' | 'NEUTRAL';
export type AssetType = 'XAUUSD' | 'XAGUSD';

export interface Prediction {
  id: string;
  asset: AssetType;
  signal: SignalType;
  confidence: number;
  price: number;
  timestamp: string;
  features?: Record<string, number>;
}

export interface WatchlistItem {
  id: string;
  asset: AssetType;
  alertPrice?: number;
  alertEnabled: boolean;
  addedAt: string;
}

export interface BacktestConfig {
  asset: AssetType;
  startDate: string;
  endDate: string;
  initialCapital: number;
  positionSize: number;
  strategyParams?: Record<string, unknown>;
}

export interface BacktestResult {
  id: string;
  config: BacktestConfig;
  metrics: {
    totalReturn: number;
    sharpeRatio: number;
    maxDrawdown: number;
    winRate: number;
    totalTrades: number;
  };
  trades: Trade[];
  equityCurve: EquityPoint[];
  createdAt: string;
}

export interface Trade {
  id: string;
  entryDate: string;
  exitDate: string;
  signal: SignalType;
  entryPrice: number;
  exitPrice: number;
  pnl: number;
  pnlPercent: number;
}

export interface EquityPoint {
  date: string;
  value: number;
}

export interface FeatureImportance {
  feature: string;
  importance: number;
  rank: number;
}

export interface ApiResponse<T = unknown> {
  data?: T;
  message?: string;
  error?: string;
  errors?: Record<string, string[]>;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface WebSocketMessage<T = unknown> {
  event: string;
  data: T;
  timestamp: string;
}
