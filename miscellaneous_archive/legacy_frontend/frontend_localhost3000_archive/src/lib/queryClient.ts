import { QueryClient, DefaultOptions } from '@tanstack/react-query';
import { handleApiError } from './axios';

/**
 * React Query Default Options
 */
const queryConfig: DefaultOptions = {
  queries: {
    // Stale time: 30 seconds
    staleTime: 30 * 1000,
    
    // Cache time: 5 minutes
    gcTime: 5 * 60 * 1000,
    
    // Retry configuration
    retry: (failureCount, error) => {
      // Don't retry on 4xx errors (client errors)
      if (error && typeof error === 'object' && 'response' in error) {
        const status = (error as { response?: { status?: number } }).response?.status;
        if (status && status >= 400 && status < 500) {
          return false;
        }
      }
      // Retry up to 2 times for other errors
      return failureCount < 2;
    },
    
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    
    // Refetch on window focus in production
    refetchOnWindowFocus: import.meta.env.PROD,
    
    // Don't refetch on mount by default
    refetchOnMount: false,
    
    // Refetch on reconnect
    refetchOnReconnect: true,
  },
  mutations: {
    // Retry mutations once
    retry: 1,
    
    // Global error handler for mutations
    onError: (error) => {
      const errorMessage = handleApiError(error);
      console.error('Mutation error:', errorMessage);
    },
  },
};

/**
 * Create Query Client Instance
 */
export const queryClient = new QueryClient({
  defaultOptions: queryConfig,
});

/**
 * Query Keys Factory
 * Centralized query key management
 */
export const queryKeys = {
  // Auth
  auth: {
    user: ['auth', 'user'] as const,
    profile: ['auth', 'profile'] as const,
  },
  
  // Trading
  trading: {
    all: ['trading'] as const,
    predictions: () => [...queryKeys.trading.all, 'predictions'] as const,
    latestPrediction: (asset?: string) => 
      [...queryKeys.trading.predictions(), 'latest', asset] as const,
    health: () => [...queryKeys.trading.all, 'health'] as const,
  },
  
  // Backtest
  backtest: {
    all: ['backtest'] as const,
    results: () => [...queryKeys.backtest.all, 'results'] as const,
    result: (id: string) => [...queryKeys.backtest.results(), id] as const,
  },
  
  // SHAP
  shap: {
    all: ['shap'] as const,
    featureImportance: (asset?: string) => 
      [...queryKeys.shap.all, 'feature-importance', asset] as const,
  },
  
  // Models
  models: {
    all: ['models'] as const,
    info: () => [...queryKeys.models.all, 'info'] as const,
  },
  
  // Watchlist
  watchlist: {
    all: ['watchlist'] as const,
    list: () => [...queryKeys.watchlist.all, 'list'] as const,
  },
  
  // Config
  config: {
    all: ['config'] as const,
    current: () => [...queryKeys.config.all, 'current'] as const,
  },
} as const;

/**
 * Helper function to invalidate all queries
 */
export function invalidateAllQueries() {
  return queryClient.invalidateQueries();
}

/**
 * Helper function to clear all queries
 */
export function clearAllQueries() {
  return queryClient.clear();
}
