// Application Constants

export const APP_CONFIG = {
  name: import.meta.env.VITE_APP_NAME || 'ML Trading Signals',
  version: import.meta.env.VITE_APP_VERSION || '1.0.0',
  apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:5000/api',
  wsUrl: import.meta.env.VITE_WS_URL || 'ws://localhost:5000',
} as const;

export const STORAGE_KEYS = {
  accessToken: 'access_token',
  refreshToken: 'refresh_token',
  user: 'user_data',
  theme: 'theme_mode',
  settings: 'user_settings',
  watchlist: 'watchlist_data',
} as const;

export const SESSION_CONFIG = {
  timeout: parseInt(import.meta.env.VITE_SESSION_TIMEOUT) || 900000, // 15 minutes
  warningTime: parseInt(import.meta.env.VITE_SESSION_WARNING_TIME) || 60000, // 1 minute
  checkInterval: 30000, // 30 seconds
} as const;

export const API_ENDPOINTS = {
  // Auth
  login: '/auth/login',
  register: '/auth/register',
  logout: '/auth/logout',
  refreshToken: '/auth/refresh',
  verifyEmail: '/auth/verify-email',
  resendOtp: '/auth/resend-otp',
  forgotPassword: '/auth/forgot-password',
  resetPassword: '/auth/reset-password',

  // User
  profile: '/profile',
  updateProfile: '/profile',
  changePassword: '/profile/password',

  // Watchlist
  watchlist: '/watchlist',

  // Trading
  predictions: '/predictions/latest',
  health: '/health',

  // Backtest
  backtestRun: '/backtest/run',
  backtestResults: '/backtest/results',

  // SHAP
  shapFeatureImportance: '/shap/feature-importance',
  shapPlot: '/shap/plot',

  // Models
  modelInfo: '/models/info',

  // Config
  config: '/config',
} as const;

export const TRADING_CONFIG = {
  defaultAsset: import.meta.env.VITE_DEFAULT_ASSET || 'XAUUSD',
  refreshInterval: parseInt(import.meta.env.VITE_REFRESH_INTERVAL) || 30000,
  assets: ['XAUUSD', 'XAGUSD'] as const,
  signals: ['BUY', 'SELL', 'NEUTRAL'] as const,
} as const;

export const WEBSOCKET_EVENTS = {
  connect: 'connect',
  disconnect: 'disconnect',
  error: 'error',
  prediction: 'prediction_update',
  price: 'price_update',
  alert: 'alert_triggered',
} as const;

export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  CONFLICT: 409,
  UNPROCESSABLE_ENTITY: 422,
  INTERNAL_SERVER_ERROR: 500,
} as const;

export const ERROR_MESSAGES = {
  networkError: 'Network error. Please check your connection.',
  unauthorized: 'Session expired. Please login again.',
  forbidden: 'You do not have permission to perform this action.',
  serverError: 'Server error. Please try again later.',
  validationError: 'Please check your input and try again.',
  unknown: 'An unexpected error occurred.',
} as const;
