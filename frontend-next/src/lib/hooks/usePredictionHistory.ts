'use client';

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api-client';

export function usePredictionHistory(days = 7, asset?: string) {
  return useQuery({
    queryKey: ['prediction-history', days, asset],
    queryFn: () => apiClient.getPredictionHistory(days, asset),
    staleTime: 30_000,
    retry: false,
  });
}
