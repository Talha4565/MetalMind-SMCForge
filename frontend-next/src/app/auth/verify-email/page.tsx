'use client';

import { useRouter } from 'next/navigation';
import { VerifyEmailForm } from '@/components/Auth/VerifyEmailForm';
import { useState } from 'react';
import { toast } from 'sonner';
import { apiClient } from '@/lib/api-client';
import { ApiError } from '@/lib/api-types';

type VerifyEmailValues = {
  email: string;
  otp_code: string;
};

/**
 * Email Verification Page.
 * Handles OTP code entry and email verification.
 */
export default function VerifyEmailPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [email, setEmail] = useState<string>(() => {
    if (typeof window === 'undefined') return '';
    const params = new URLSearchParams(window.location.search);
    return params.get('email') ? decodeURIComponent(params.get('email')!) : '';
  });

  const handleVerifyEmail = async (values: VerifyEmailValues) => {
    setIsLoading(true);
    
    try {
      const response = await apiClient.verifyEmail({
        email: email || values.email,
        otp_code: values.otp_code,
      });

      if (response.success) {
        toast.success(response.message || 'Email verified successfully!');
        
        // Navigate to the completion page
        setTimeout(() => {
          router.push(`/auth/verify-success?email=${encodeURIComponent(email || values.email)}`);
        }, 700);
      } else {
        toast.error(response.message || 'Verification failed');
      }
    } catch (error: unknown) {
      const apiErr = error as ApiError;
      const errorMsg = apiErr.error || (error instanceof Error ? error.message : 'Verification failed. Please try again.');
      toast.error(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResendOTP = async (resendEmail: string) => {
    if (!resendEmail) {
      toast.error('Email address is required');
      return;
    }

    setIsLoading(true);
    
    try {
      const response = await apiClient.resendOTP({
        email: resendEmail,
      });

      if (response.success) {
        toast.success('OTP sent successfully! Check your email.');
        setEmail(resendEmail);
      } else {
        toast.error('Failed to resend OTP');
      }
    } catch (error: unknown) {
      const errorMsg = (error as ApiError).error || (error instanceof Error ? error.message : 'Failed to resend OTP');
      toast.error(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      {/* Visual background elements */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-emerald-600/10 rounded-full blur-[128px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-teal-600/10 rounded-full blur-[128px] pointer-events-none" />
      
      <div className="relative z-10 w-full max-w-md">
        <VerifyEmailForm 
          onSubmit={handleVerifyEmail}
          onResendOTP={handleResendOTP}
          email={email}
          isLoading={isLoading}
        />
      </div>
    </div>
  );
}
