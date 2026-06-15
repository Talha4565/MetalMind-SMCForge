import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import {
  AuthResponse,
  LoginPayload,
  RegisterPayload,
  PredictionResponse,
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
  private token: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      // Timeout after 10 seconds
      timeout: 10000,
    });

    // Initialize in-memory token from localStorage for reloads.
    const savedToken = this.getToken();
    if (savedToken) {
      this.token = savedToken;
    }

    // Request Interceptor: Attach JWT token
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const token = this.getToken();
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response Interceptor: Handle errors globally
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response) {
          // Handle specific status codes
          if (error.response.status === 401) {
            this.clearAuth();
            // In a real app, we might trigger a redirect to login here
            // via a callback or event bus if not using NextAuth middleware
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

  // --- Auth Management ---

  setToken(token: string) {
    this.token = token;
    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_token', token);
    }
  }

  getToken(): string | null {
    if (this.token) return this.token;
    if (typeof window !== 'undefined') {
      return localStorage.getItem('auth_token');
    }
    return null;
  }

  clearAuth() {
    this.token = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token');
    }
  }

  // --- API Endpoints ---

  // Auth
  async login(payload: LoginPayload): Promise<AuthResponse> {
    const response = await this.client.post<AuthResponse>('/api/auth/login', payload);
    if (response.data.token) {
      this.setToken(response.data.token);
    }
    return response.data;
  }

  async register(payload: RegisterPayload): Promise<AuthResponse> {
    const response = await this.client.post<AuthResponse>('/api/auth/register', payload);
    return response.data;
  }

  // Predictions
  async getLatestPrediction(asset: AssetType): Promise<PredictionResponse> {
    const response = await this.client.get<PredictionResponse>(`/api/predictions/latest?asset=${asset}`);
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

  async getBacktestResults(): Promise<BacktestResponse[]> {
    const response = await this.client.get<BacktestResponse[]>('/api/backtest/results');
    return response.data;
  }

  // Profile
  async updateProfile(data: { email?: string }): Promise<{ message: string; profile: Profile }> {
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
