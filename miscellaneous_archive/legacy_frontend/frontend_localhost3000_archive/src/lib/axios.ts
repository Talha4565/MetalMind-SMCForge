import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { tokenManager } from './tokenManager';
import { APP_CONFIG, API_ENDPOINTS, HTTP_STATUS, ERROR_MESSAGES } from '@/config/constants';
import type { ApiResponse } from '@/types';

/**
 * Axios client with interceptors
 * - Auto-attach JWT tokens
 * - Handle token refresh
 * - Global error handling
 * - Request cancellation support
 */

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: APP_CONFIG.apiUrl,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Send cookies with requests
});

// Request interceptor - Attach access token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = tokenManager.getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Response interceptor - Handle token refresh
apiClient.interceptors.response.use(
  response => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Handle 401 Unauthorized
    if (error.response?.status === HTTP_STATUS.UNAUTHORIZED && !originalRequest._retry) {
      originalRequest._retry = true;

      // Check if we have a refresh token
      const refreshToken = tokenManager.getRefreshToken();
      if (!refreshToken) {
        // No refresh token, clear auth and reject
        tokenManager.clearTokens();
        window.location.href = '/login';
        return Promise.reject(error);
      }

      try {
        // Check if there's already a refresh in progress
        let refreshPromise = tokenManager.getRefreshPromise();

        if (!refreshPromise) {
          // Create new refresh promise
          refreshPromise = refreshAccessToken(refreshToken);
          tokenManager.setRefreshPromise(refreshPromise);
        }

        // Wait for refresh to complete
        const newAccessToken = await refreshPromise;
        tokenManager.clearRefreshPromise();

        // Update token in original request
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;

        // Retry original request
        return apiClient(originalRequest);
      } catch (refreshError) {
        // Refresh failed, clear tokens and redirect to login
        tokenManager.clearTokens();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

/**
 * Refresh access token
 */
async function refreshAccessToken(refreshToken: string): Promise<string> {
  try {
    const response = await axios.post<ApiResponse<{ accessToken: string }>>(
      `${APP_CONFIG.apiUrl}${API_ENDPOINTS.refreshToken}`,
      { refreshToken },
      {
        headers: {
          'Content-Type': 'application/json',
        },
        withCredentials: true,
      }
    );

    const newAccessToken = response.data.data?.accessToken;
    if (!newAccessToken) {
      throw new Error('No access token in refresh response');
    }

    // Update token
    tokenManager.updateAccessToken(newAccessToken);

    return newAccessToken;
  } catch (error) {
    console.error('Token refresh failed:', error);
    throw error;
  }
}

/**
 * Error handler helper
 */
export function handleApiError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<ApiResponse>;

    // Network error
    if (!axiosError.response) {
      return ERROR_MESSAGES.networkError;
    }

    // Handle different status codes
    switch (axiosError.response.status) {
      case HTTP_STATUS.UNAUTHORIZED:
        return ERROR_MESSAGES.unauthorized;
      case HTTP_STATUS.FORBIDDEN:
        return ERROR_MESSAGES.forbidden;
      case HTTP_STATUS.BAD_REQUEST:
      case HTTP_STATUS.UNPROCESSABLE_ENTITY:
        return axiosError.response.data?.error || ERROR_MESSAGES.validationError;
      case 429: // Rate limit exceeded
        return 'Too many requests. Please wait a moment and try again.';
      case HTTP_STATUS.INTERNAL_SERVER_ERROR:
        return ERROR_MESSAGES.serverError;
      default:
        return axiosError.response.data?.error || ERROR_MESSAGES.unknown;
    }
  }

  if (error instanceof Error) {
    return error.message;
  }

  return ERROR_MESSAGES.unknown;
}

/**
 * Create cancellable request
 */
export function createCancelToken() {
  return axios.CancelToken.source();
}

/**
 * Check if error is cancel error
 */
export function isCancelError(error: unknown): boolean {
  return axios.isCancel(error);
}

export default apiClient;
