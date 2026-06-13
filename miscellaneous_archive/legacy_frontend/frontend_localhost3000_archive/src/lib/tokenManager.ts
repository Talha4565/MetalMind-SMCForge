import { secureStorage } from './secureStorage';
import { STORAGE_KEYS } from '@/config/constants';
import type { AuthTokens, User } from '@/types';

/**
 * Token Manager
 * Handles JWT token storage, retrieval, and refresh logic
 */
class TokenManager {
  private accessToken: string | null = null;
  private refreshToken: string | null = null;
  private tokenRefreshPromise: Promise<string> | null = null;

  constructor() {
    // Load tokens from storage on initialization
    this.loadTokens();
  }

  private loadTokens(): void {
    try {
      this.accessToken = secureStorage.getItem(STORAGE_KEYS.accessToken);
      this.refreshToken = secureStorage.getItem(STORAGE_KEYS.refreshToken);
    } catch (error) {
      console.error('Failed to load tokens:', error);
      this.clearTokens();
    }
  }

  // Set tokens (after login/register)
  setTokens(tokens: AuthTokens): void {
    try {
      this.accessToken = tokens.accessToken;
      this.refreshToken = tokens.refreshToken;

      secureStorage.setItem(STORAGE_KEYS.accessToken, tokens.accessToken);
      secureStorage.setItem(STORAGE_KEYS.refreshToken, tokens.refreshToken);
    } catch (error) {
      console.error('Failed to set tokens:', error);
      throw error;
    }
  }

  // Get access token
  getAccessToken(): string | null {
    return this.accessToken;
  }

  // Get refresh token
  getRefreshToken(): string | null {
    return this.refreshToken;
  }

  // Clear all tokens
  clearTokens(): void {
    this.accessToken = null;
    this.refreshToken = null;
    this.tokenRefreshPromise = null;

    secureStorage.removeItem(STORAGE_KEYS.accessToken);
    secureStorage.removeItem(STORAGE_KEYS.refreshToken);
    secureStorage.removeItem(STORAGE_KEYS.user);
  }

  // Check if user is authenticated
  isAuthenticated(): boolean {
    return this.accessToken !== null;
  }

  // Decode JWT (without verification - for client-side use only)
  private decodeToken(token: string): Record<string, unknown> | null {
    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      return JSON.parse(jsonPayload);
    } catch (error) {
      console.error('Token decode error:', error);
      return null;
    }
  }

  // Check if token is expired
  isTokenExpired(token: string): boolean {
    try {
      const decoded = this.decodeToken(token);
      if (!decoded || !decoded.exp) {
        return true;
      }
      const expirationTime = (decoded.exp as number) * 1000; // Convert to milliseconds
      const currentTime = Date.now();
      // Consider token expired 30 seconds before actual expiration
      return currentTime >= expirationTime - 30000;
    } catch (error) {
      return true;
    }
  }

  // Check if access token needs refresh
  needsRefresh(): boolean {
    if (!this.accessToken) {
      return false;
    }
    return this.isTokenExpired(this.accessToken);
  }

  // Set refresh promise (to prevent multiple refresh calls)
  setRefreshPromise(promise: Promise<string>): void {
    this.tokenRefreshPromise = promise;
  }

  // Get refresh promise
  getRefreshPromise(): Promise<string> | null {
    return this.tokenRefreshPromise;
  }

  // Clear refresh promise
  clearRefreshPromise(): void {
    this.tokenRefreshPromise = null;
  }

  // Store user data
  setUser(user: User): void {
    try {
      secureStorage.setObject(STORAGE_KEYS.user, user);
    } catch (error) {
      console.error('Failed to store user:', error);
    }
  }

  // Get user data
  getUser(): User | null {
    try {
      return secureStorage.getObject<User>(STORAGE_KEYS.user);
    } catch (error) {
      console.error('Failed to get user:', error);
      return null;
    }
  }

  // Update access token (after refresh)
  updateAccessToken(token: string): void {
    this.accessToken = token;
    secureStorage.setItem(STORAGE_KEYS.accessToken, token);
  }
}

export const tokenManager = new TokenManager();
