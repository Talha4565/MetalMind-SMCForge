import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import { tokenManager } from '@/lib/tokenManager';
import { socketManager } from '@/lib/socket';
import type { User, AuthTokens } from '@/types';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

interface AuthActions {
  setUser: (user: User) => void;
  setTokens: (tokens: AuthTokens) => void;
  login: (user: User, tokens: AuthTokens) => void;
  logout: () => void;
  updateUser: (updates: Partial<User>) => void;
  clearError: () => void;
  setError: (error: string) => void;
  setLoading: (loading: boolean) => void;
  initializeAuth: () => void;
}

type AuthStore = AuthState & AuthActions;

/**
 * Auth Store
 * Manages authentication state with Zustand + Immer
 */
export const useAuthStore = create<AuthStore>()(
  immer((set) => ({
    // State
    user: null,
    isAuthenticated: false,
    isLoading: false,
    error: null,

    // Actions
    setUser: (user) =>
      set((state) => {
        state.user = user;
        state.isAuthenticated = true;
        tokenManager.setUser(user);
      }),

    setTokens: (tokens) => {
      tokenManager.setTokens(tokens);
    },

    login: (user, tokens) =>
      set((state) => {
        state.user = user;
        state.isAuthenticated = true;
        state.error = null;
        
        // Store tokens
        tokenManager.setTokens(tokens);
        tokenManager.setUser(user);
        
        // Connect to WebSocket
        socketManager.connect();
      }),

    logout: () =>
      set((state) => {
        state.user = null;
        state.isAuthenticated = false;
        state.error = null;
        
        // Clear tokens
        tokenManager.clearTokens();
        
        // Disconnect WebSocket
        socketManager.disconnect();
      }),

    updateUser: (updates) =>
      set((state) => {
        if (state.user) {
          state.user = { ...state.user, ...updates };
          tokenManager.setUser(state.user);
        }
      }),

    clearError: () =>
      set((state) => {
        state.error = null;
      }),

    setError: (error) =>
      set((state) => {
        state.error = error;
      }),

    setLoading: (loading) =>
      set((state) => {
        state.isLoading = loading;
      }),

    initializeAuth: () =>
      set((state) => {
        // Check if user is already authenticated
        const user = tokenManager.getUser();
        const isAuthenticated = tokenManager.isAuthenticated();

        if (user && isAuthenticated) {
          state.user = user;
          state.isAuthenticated = true;
          
          // Auto-connect to WebSocket if authenticated
          socketManager.connect();
        }
      }),
  }))
);

// Initialize auth state on app load
useAuthStore.getState().initializeAuth();
