import { useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import {
  Box,
  Container,
  Typography,
  Paper,
  Button,
  Link,
  Alert,
  CircularProgress,
} from '@mui/material';
import LockResetIcon from '@mui/icons-material/LockReset';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import { FormInput } from '@/components/common';
import { forgotPasswordSchema, type ForgotPasswordFormData } from '@/features/auth/utils/validation';
import { apiClient, handleApiError } from '@/api/client';
import { API_ENDPOINTS } from '@/config/constants';
import { toast } from 'react-toastify';

export function ForgotPassword() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [emailSent, setEmailSent] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { control, handleSubmit } = useForm<ForgotPasswordFormData>({
    resolver: zodResolver(forgotPasswordSchema),
    defaultValues: {
      email: '',
    },
  });

  const onSubmit = async (data: ForgotPasswordFormData) => {
    try {
      setIsSubmitting(true);
      setError(null);

      await apiClient.post(API_ENDPOINTS.forgotPassword, data);

      setEmailSent(true);
      toast.success('Password reset instructions sent to your email');
    } catch (err) {
      const message = handleApiError(err);
      setError(message);
      toast.error(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Container maxWidth="sm">
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          py: 4,
        }}
      >
        <Paper
          elevation={3}
          sx={{
            p: 4,
            width: '100%',
            borderRadius: 2,
          }}
        >
          {/* Header */}
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mb: 3 }}>
            <Box
              sx={{
                width: 48,
                height: 48,
                borderRadius: '50%',
                bgcolor: 'primary.main',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                mb: 1,
              }}
            >
              <LockResetIcon sx={{ color: 'white', fontSize: 28 }} />
            </Box>
            <Typography variant="h4" component="h1" fontWeight={600}>
              Forgot Password?
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1, textAlign: 'center' }}>
              {emailSent
                ? 'Check your email for reset instructions'
                : 'Enter your email to receive password reset instructions'}
            </Typography>
          </Box>

          {/* Success Message */}
          {emailSent ? (
            <Box>
              <Alert severity="success" sx={{ mb: 3 }}>
                We've sent password reset instructions to your email. Please check your inbox and
                follow the link to reset your password.
              </Alert>
              <Button
                component={RouterLink}
                to="/login"
                variant="contained"
                fullWidth
                size="large"
                sx={{ py: 1.5 }}
              >
                Back to Login
              </Button>
            </Box>
          ) : (
            <>
              {/* Error Alert */}
              {error && (
                <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 3 }}>
                  {error}
                </Alert>
              )}

              {/* Form */}
              <Box component="form" onSubmit={handleSubmit(onSubmit)} noValidate>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
                  <FormInput
                    name="email"
                    control={control}
                    label="Email Address"
                    type="email"
                    placeholder="you@example.com"
                    autoComplete="email"
                    disabled={isSubmitting}
                  />

                  <Button
                    type="submit"
                    variant="contained"
                    size="large"
                    fullWidth
                    disabled={isSubmitting}
                    sx={{ mt: 1, py: 1.5 }}
                  >
                    {isSubmitting ? (
                      <>
                        <CircularProgress size={20} sx={{ mr: 1 }} />
                        Sending...
                      </>
                    ) : (
                      'Send Reset Link'
                    )}
                  </Button>
                </Box>
              </Box>
            </>
          )}

          {/* Back to Login */}
          {!emailSent && (
            <Box sx={{ mt: 3, textAlign: 'center' }}>
              <Link
                component={RouterLink}
                to="/login"
                variant="body2"
                underline="hover"
                sx={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 0.5,
                  fontWeight: 500,
                }}
              >
                <ArrowBackIcon fontSize="small" />
                Back to Login
              </Link>
            </Box>
          )}
        </Paper>
      </Box>
    </Container>
  );
}
