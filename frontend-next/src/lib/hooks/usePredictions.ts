'use client';

import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { apiClient } from '../api-client';
import { PredictionResponse, AssetType } from '../api-types';
import { useSession } from 'next-auth/react';

type SessionWithToken = {
  accessToken?: string;
};

/**
 * Hook to fetch the latest predictions for a specific asset.
 * Uses TanStack Query for caching and automatic re-fetching.
 * retry: 0 so offline API falls through immediately to mock data.
 */

export function usePredictions(asset: AssetType): UseQueryResult<PredictionResponse, Error> {
  const { data: session } = useSession();
  const accessToken = (session as SessionWithToken)?.accessToken;

  if (accessToken && apiClient.getToken() !== accessToken) {
    apiClient.setToken(accessToken);
  }

  return useQuery({
    queryKey: ['predictions', asset],
    queryFn: () => apiClient.getLatestPrediction(asset),
    refetchInterval: 60000,
    staleTime: 30000,
    retry: 0,
    enabled: true,
  });
}
