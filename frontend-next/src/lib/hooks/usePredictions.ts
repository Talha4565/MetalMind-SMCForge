'use client';

import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { apiClient } from '../api-client';
import { PredictionResponse, AssetType } from '../api-types';

/**
 * Hook to fetch the latest predictions for a specific asset.
 * Uses TanStack Query for caching and automatic re-fetching.
 * retry: 0 so offline API falls through immediately to mock data.
 */

export function usePredictions(asset: AssetType): UseQueryResult<PredictionResponse, Error> {
  return useQuery({
    queryKey: ['predictions', asset],
    queryFn: () => apiClient.getLatestPrediction(asset),
    refetchInterval: 60000,
    staleTime: 30000,
    retry: 0,
    enabled: true,
  });
}
