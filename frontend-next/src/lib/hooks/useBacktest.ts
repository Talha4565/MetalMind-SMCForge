import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../api-client';
import { BacktestRequest } from '../api-types';

/**
 * Hook to run a new backtest simulation.
 */
export function useRunBacktest() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: BacktestRequest) => apiClient.runBacktest(payload),
    onSuccess: () => {
      // Refresh the history list after a successful run
      queryClient.invalidateQueries({ queryKey: ['backtest-results'] });
    },
  });
}

/**
 * Hook to fetch previous backtest results history.
 */
export function useBacktestHistory() {
  return useQuery({
    queryKey: ['backtest-results'],
    queryFn: () => apiClient.getBacktestResults(),
    staleTime: 5 * 60 * 1000, // History is stable for 5 minutes
  });
}
