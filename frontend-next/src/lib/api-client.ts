import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import {
  AuthResponse,
  LoginPayload,
  RegisterPayload,
  PredictionResponse,
  PredictionHistoryResponse,
  AssetType,
  BacktestRequest,
  BacktestResponse,
  WatchlistItem,
  WatchlistResponse,
  SymbolsResponse,
  Profile,
} from './api-types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

class ApiClient {
  private client: AxiosInstance;
  private accessToken: string | null = null;
  private refreshToken: string | null = null;
  private isRefreshing = false;
  private refreshPromise: Promise<string | null> | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 10000,
      withCredentials: true,
    });

    // Request Interceptor: Attach JWT from memory only (never localStorage)
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        if (this.accessToken && config.headers) {
          config.headers.Authorization = `Bearer ${this.accessToken}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response Interceptor: Handle 401 with silent token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response) {
          // Handle 401 — try refresh before redirecting
          if (error.response.status === 401 && !error.config._retry) {
            if (this.refreshToken) {
              // Attempt silent token refresh
              const newToken = await this._silentRefresh();
              if (newToken) {
                // Retry original request with new token
                error.config._retry = true;
                error.config.headers.Authorization = `Bearer ${newToken}`;
                return this.client.request(error.config);
              }
            }

            if (this.accessToken) {
              // Refresh failed — genuinely expired, redirect to login
              this.clearAuth();
              if (typeof window !== 'undefined') {
                window.location.href = '/auth/login';
              }
            }
            // else: no token set yet — auth sync hasn't fired, just reject
          }
          
          // Format the error for easier consumption
          const apiError = {
            error: error.response.data.error || 'An unexpected error occurred',
            details: error.response.data.details || '',
            status: error.response.status,
            timestamp: new Date().toISOString(),
          };
          return Promise.reject(apiError);
        }
        
        // Handle network or other errors
        return Promise.reject({
          error: error.message || 'Network error',
          status: 0,
          timestamp: new Date().toISOString(),
        });
      }
    );
  }

  // --- Auth Management (memory-only, never localStorage) ---

  setTokens(accessToken: string, refreshToken?: string) {
    this.accessToken = accessToken;
    if (refreshToken) this.refreshToken = refreshToken;
  }

  setAccessToken(token: string) {
    this.accessToken = token;
  }

  clearAuth() {
    this.accessToken = null;
    this.refreshToken = null;
  }

  /** Silently refresh the access token. Returns new token or null. */
  private async _silentRefresh(): Promise<string | null> {
    // Deduplicate concurrent refresh attempts
    if (this.isRefreshing && this.refreshPromise) {
      return this.refreshPromise;
    }

    this.isRefreshing = true;
    this.refreshPromise = (async () => {
      try {
        const response = await axios.post(`${API_BASE_URL}/api/auth/refresh`, {
          refresh_token: this.refreshToken,
        }, { timeout: 8000, withCredentials: true });

        if (response.data?.access_token) {
          this.accessToken = response.data.access_token;
          return response.data.access_token;
        }
        return null;
      } catch {
        return null;
      } finally {
        this.isRefreshing = false;
        this.refreshPromise = null;
      }
    })();

    return this.refreshPromise;
  }

  // --- API Endpoints ---

  // Auth
  async login(payload: LoginPayload): Promise<AuthResponse> {
    const response = await this.client.post<AuthResponse>('/api/auth/login', payload);
    if (response.data.token) {
      this.setAccessToken(response.data.token);
    }
    return response.data;
  }

  async register(payload: RegisterPayload): Promise<AuthResponse> {
    const response = await this.client.post<AuthResponse>('/api/auth/register', payload);
    return response.data;
  }

  async forgotPassword(email: string): Promise<{ message: string }> {
    const response = await this.client.post<{ message: string }>('/api/auth/forgot-password', { email });
    return response.data;
  }

  async resetPassword(token: string, password: string): Promise<{ message: string }> {
    const response = await this.client.post<{ message: string }>('/api/auth/reset-password', { token, password });
    return response.data;
  }

  // Predictions
  async getLatestPrediction(asset: AssetType): Promise<PredictionResponse> {
    const response = await this.client.get<PredictionResponse>(`/api/predictions/latest?asset=${asset}`, { timeout: 60000 });
    return response.data;
  }

  async getPredictionHistory(days = 7, asset?: string): Promise<PredictionHistoryResponse> {
    const params = new URLSearchParams({ days: String(days) });
    if (asset) params.set('asset', asset);
    const response = await this.client.get<PredictionHistoryResponse>(`/api/predictions/history?${params}`);
    return response.data;
  }

  // Live Price
  async getLivePrice(asset: AssetType): Promise<{ asset: string; price: number; timestamp: string }> {
    const response = await this.client.get<{ asset: string; price: number; timestamp: string }>(`/api/market/price?asset=${asset}`);
    return response.data;
  }

  // Watchlist
  async getWatchlist(): Promise<WatchlistResponse> {
    const response = await this.client.get<WatchlistResponse>('/api/watchlist');
    return response.data;
  }

  async getWatchlistSymbols(): Promise<SymbolsResponse> {
    const response = await this.client.get<SymbolsResponse>('/api/watchlist/symbols');
    return response.data;
  }

  async addWatchlistItem(data: {
    symbol: string;
    display_name?: string;
    notifications_enabled?: boolean;
    alert_threshold?: number | null;
    notes?: string;
  }): Promise<{ message: string; item: WatchlistItem }> {
    const response = await this.client.post<{ message: string; item: WatchlistItem }>('/api/watchlist', data);
    return response.data;
  }

  async removeWatchlistItem(itemId: number): Promise<{ message: string }> {
    const response = await this.client.delete<{ message: string }>(`/api/watchlist/${itemId}`);
    return response.data;
  }

  // Backtesting
  async runBacktest(payload: BacktestRequest): Promise<BacktestResponse> {
    const response = await this.client.post<BacktestResponse>('/api/backtest/run', payload);
    return response.data;
  }

  async getBacktestStatus(): Promise<{ running: boolean; progress: number; error: string | null; result: unknown }> {
    const response = await this.client.get('/api/backtest/status');
    return response.data;
  }

  async getBacktestResults(): Promise<BacktestResponse[]> {
    const response = await this.client.get('/api/backtest/results');
    const data = response.data;
    if (Array.isArray(data)) return data;
    if (data && typeof data === 'object') {
      // Backend may return { summary: {...}, trades: [...] } or flat { win_rate, ... }
      const s = data.summary || data;
      return [{
        asset: data.asset || s.asset || undefined,
        win_rate: s.win_rate ?? 0,
        profit_factor: s.profit_factor ?? 0,
        max_drawdown: s.max_drawdown ?? s.max_drawdown_pct ?? 0,
        total_trades: s.total_trades ?? s.n_trades ?? 0,
        net_profit: s.net_profit ?? s.total_return_usd ?? 0,
        sharpe_ratio: s.sharpe_ratio ?? 0,
        sortino_ratio: s.sortino_ratio ?? 0,
        calmar_ratio: s.calmar_ratio ?? 0,
        trades: data.trades || [],
      }];
    }
    return [];
  }

  async exportBacktest(format: 'csv' | 'pdf', type: string = 'all'): Promise<Blob> {
    const response = await this.client.get(`/api/backtest/export?format=${format}&type=${type}`, {
      responseType: 'blob',
    });
    return response.data;
  }

  // Pipeline
  async getPipelineStatus(): Promise<any> {
    const response = await this.client.get('/api/pipeline/status');
    return response.data;
  }

  async getPipelineDetails(): Promise<any> {
    const response = await this.client.get('/api/pipeline/details');
    return response.data;
  }

  async triggerPipeline(type: string, asset: string): Promise<any> {
    const response = await this.client.post('/api/pipeline/run', { type, asset });
    return response.data;
  }

  // Profile
  async updateProfile(data: { name?: string; email?: string }): Promise<{ message: string; profile: Profile }> {
    const response = await this.client.put<{ message: string; profile: Profile }>('/api/profile', data);
    return response.data;
  }

  async changePassword(data: { current_password: string; new_password: string }): Promise<{ message: string }> {
    const response = await this.client.put<{ message: string }>('/api/profile/password', data);
    return response.data;
  }

  async getProfile(): Promise<{ profile: Profile }> {
    const response = await this.client.get<{ profile: Profile }>('/api/profile');
    return response.data;
  }

  async uploadAvatar(file: File): Promise<{ message: string; profile: Profile; avatar_url?: string }> {
    const form = new FormData();
    form.append('avatar', file);
    const response = await this.client.put<{ message: string; profile: Profile; avatar_url?: string }>('/api/profile/avatar', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  }

  // 2FA (TOTP)
  async get2faSetup(): Promise<{ secret: string; provisioning_uri: string; qr: string }> {
    const response = await this.client.get<{ secret: string; provisioning_uri: string; qr: string }>('/api/profile/2fa/setup');
    return response.data;
  }

  async enable2fa(otp: string): Promise<{ success: boolean; message: string }> {
    const response = await this.client.post<{ success: boolean; message: string }>('/api/profile/2fa/enable', { otp });
    return response.data;
  }

  async disable2fa(otp: string): Promise<{ success: boolean; message: string }> {
    const response = await this.client.post<{ success: boolean; message: string }>('/api/profile/2fa/disable', { otp });
    return response.data;
  }

  // Settings
  async getSettings(): Promise<{ settings: Record<string, unknown> }> {
    const response = await this.client.get<{ settings: Record<string, unknown> }>('/api/profile/settings');
    return response.data;
  }

  async updateSettings(data: Record<string, unknown>): Promise<{ message: string; settings: Record<string, unknown> }> {
    const response = await this.client.put<{ message: string; settings: Record<string, unknown> }>('/api/profile/settings', data);
    return response.data;
  }

  // Account
  async deleteAccount(password: string): Promise<{ message: string }> {
    const response = await this.client.delete<{ message: string }>('/api/profile/delete', { data: { password } });
    return response.data;
  }

  async verifyEmail(data: { email: string; otp_code: string }): Promise<{ success: boolean; message: string }> {
    const response = await this.client.post<{ success: boolean; message: string }>('/api/auth/verify-email', data);
    return response.data;
  }

  async resendOTP(data: { email: string }): Promise<{ success: boolean; message: string }> {
    const response = await this.client.post<{ success: boolean; message: string }>('/api/auth/resend-otp', data);
    return response.data;
  }
}

// Export a singleton instance
export const apiClient = new ApiClient();
