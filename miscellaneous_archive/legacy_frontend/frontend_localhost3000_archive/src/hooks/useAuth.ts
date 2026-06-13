import { useCallback } from 'react';
import { useAuthStore } from '@/features/auth/store/authStore';
import { useMutation } from '@tanstack/react-query';
import { apiClient, handleApiError } from '@/api/client';
import { API_ENDPOINTS } from '@/config/constants';
import { toast } from 'react-toastify';
import type { LoginCredentials, RegisterData, OTPVerification, User, AuthTokens, ApiResponse } from '@/types';

/**
 * useAuth Hook
 * Provides authentication operations
 */
export function useAuth() {
  const { 
    user, 
    isAuthenticated, 
    isLoading,
    error,
    login: loginStore, 
    logout: logoutStore,
    setLoading,
    setError,
    clearError,
  } = useAuthStore();

  // Login mutation
  const loginMutation = useMutation({
    mutationFn: async (credentials: LoginCredentials) => {
      setLoading(true);
      clearError();
      
      const response = await apiClient.post<ApiResponse<{ user: User; tokens: AuthTokens }>>(
        API_ENDPOINTS.login,
        credentials
      );
      
      return response.data.data!;
    },
    onSuccess: (data) => {
      loginStore(data.user, data.tokens);
      toast.success('Login successful!');
      setLoading(false);
    },
    onError: (error) => {
      const message = handleApiError(error);
      setError(message);
      toast.error(message);
      setLoading(false);
    },
  });

  // Register mutation
  const registerMutation = useMutation({
    mutationFn: async (data: RegisterData) => {
      setLoading(true);
      clearError();
      
      const response = await apiClient.post<ApiResponse<{ message: string }>>(
        API_ENDPOINTS.register,
        data
      );
      
      return response.data;
    },
    onSuccess: (data) => {
      toast.success(data.message || 'Registration successful! Please verify your email.');
      setLoading(false);
    },
    onError: (error) => {
      const message = handleApiError(error);
      setError(message);
      toast.error(message);
      setLoading(false);
    },
  });

  // Verify email mutation
  const verifyEmailMutation = useMutation({
    mutationFn: async (data: OTPVerification) => {
      setLoading(true);
      clearError();
      
      const response = await apiClient.post<ApiResponse<{ user: User; tokens: AuthTokens }>>(
        API_ENDPOINTS.verifyEmail,
        data
      );
      
      return response.data.data!;
    },
    onSuccess: (data) => {
      loginStore(data.user, data.tokens);
      toast.success('Email verified successfully!');
      setLoading(false);
    },
    onError: (error) => {
      const message = handleApiError(error);
      setError(message);
      toast.error(message);
      setLoading(false);
    },
  });

  // Resend OTP mutation
  const resendOtpMutation = useMutation({
    mutationFn: async (email: string) => {
      const response = await apiClient.post<ApiResponse<{ message: string }>>(
        API_ENDPOINTS.resendOtp,
        { email }
      );
      
      return response.data;
    },
    onSuccess: (data) => {
      toast.success(data.message || 'OTP sent successfully!');
    },
    onError: (error) => {
      const message = handleApiError(error);
      toast.error(message);
    },
  });

  // Logout function
  const logout = useCallback(() => {
    logoutStore();
    toast.info('Logged out successfully');
  }, [logoutStore]);

  // Login wrapper
  const login = useCallback((credentials: LoginCredentials) => {
    return loginMutation.mutateAsync(credentials);
  }, [loginMutation]);

  // Register wrapper
  const register = useCallback((data: RegisterData) => {
    return registerMutation.mutateAsync(data);
  }, [registerMutation]);

  // Verify email wrapper
  const verifyEmail = useCallback((data: OTPVerification) => {
    return verifyEmailMutation.mutateAsync(data);
  }, [verifyEmailMutation]);

  // Resend OTP wrapper
  const resendOtp = useCallback((email: string) => {
    return resendOtpMutation.mutateAsync(email);
  }, [resendOtpMutation]);

  return {
    // State
    user,
    isAuthenticated,
    isLoading: isLoading || loginMutation.isPending || registerMutation.isPending,
    error,
    
    // Actions
    login,
    logout,
    register,
    verifyEmail,
    resendOtp,
    clearError,
    
    // Mutation states
    isLoginPending: loginMutation.isPending,
    isRegisterPending: registerMutation.isPending,
    isVerifyPending: verifyEmailMutation.isPending,
  };
}
