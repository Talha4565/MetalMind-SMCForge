import { useState } from 'react';
import { useNavigate, useSearchParams, Link as RouterLink } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import {
  Box,
  Container,
  Typography,
  Paper,
  Button,
  Alert,
  CircularProgress,
  Link,
} from '@mui/material';
import LockResetIcon from '@mui/icons-material/LockReset';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import { PasswordInput } from '@/components/common';
import { resetPasswordSchema, type ResetPasswordFormData } from '@/features/auth/utils/validation';
import { apiClient, handleApiError } from '@/api/client';
import { API_ENDPOINTS } from '@/config/constants';
import { toast } from 'react-toastify';

export function ResetPassword() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') || '';
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { control, handleSubmit } = useForm<ResetPasswordFormData>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: {
      password: '',
      confirmPassword: '',
      token,
    },
  });

  const onSubmit = async (data: ResetPasswordFormData) => {
    try {
      setIsSubmitting(true);
      setError(null);

      await apiClient.post(API_ENDPOINTS.resetPassword, {
        token: data.token,
        password: data.password,
      });

      setSuccess(true);
      toast.success('Password reset successful!');
      
      // Redirect to login after 3 seconds
      setTimeout(() => {
        navigate('/login');
      }, 3000);
    } catch (err) {
      const message = handleApiError(err);
      setError(message);
      toast.error(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Check if token is missing
  if (!token) {
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
          <Paper elevation={3} sx={{ p: 4, width: '100%', borderRadius: 2 }}>
            <Alert severity="error">
              Invalid or missing reset token. Please request a new password reset link.
            </Alert>
            <Button
              component={RouterLink}
              to="/forgot-password"
              variant="contained"
              fullWidth
              sx={{ mt: 2 }}
            >
              Request New Link
            </Button>
          </Paper>
        </Box>
      </Container>
    );
  }

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
        <Paper elevation={3} sx={{ p: 4, width: '100%', borderRadius: 2 }}>
          {/* Header */}
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mb: 3 }}>
            <Box
              sx={{
                width: 48,
                height: 48,
                borderRadius: '50%',
                bgcolor: success ? 'success.main' : 'primary.main',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                mb: 1,
              }}
            >
              {success ? (
                <CheckCircleIcon sx={{ color: 'white', fontSize: 28 }} />
              ) : (
                <LockResetIcon sx={{ color: 'white', fontSize: 28 }} />
              )}
            </Box>
            <Typography variant="h4" component="h1" fontWeight={600}>
              {success ? 'Password Reset!' : 'Reset Password'}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1, textAlign: 'center' }}>
              {success
                ? 'Your password has been successfully reset'
                : 'Enter your new password below'}
            </Typography>
          </Box>

          {/* Success Message */}
          {success ? (
            <Box>
              <Alert severity="success" sx={{ mb: 3 }}>
                Your password has been reset successfully. You can now login with your new password.
              </Alert>
              <Button
                component={RouterLink}
                to="/login"
                variant="contained"
                fullWidth
                size="large"
                sx={{ py: 1.5 }}
              >
                Go to Login
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
                  <PasswordInput
                    name="password"
                    control={control}
                    label="New Password"
                    placeholder="Enter your new password"
                    autoComplete="new-password"
                    showStrength
                    disabled={isSubmitting}
                  />

                  <PasswordInput
                    name="confirmPassword"
                    control={control}
                    label="Confirm New Password"
                    placeholder="Re-enter your new password"
                    autoComplete="new-password"
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
                        Resetting Password...
                      </>
                    ) : (
                      'Reset Password'
                    )}
                  </Button>
                </Box>
              </Box>

              {/* Back to Login */}
              <Box sx={{ mt: 3, textAlign: 'center' }}>
                <Typography variant="body2" color="text.secondary">
                  Remember your password?{' '}
                  <Link
                    component={RouterLink}
                    to="/login"
                    variant="body2"
                    underline="hover"
                    fontWeight={600}
                  >
                    Sign in
                  </Link>
                </Typography>
              </Box>
            </>
          )}
        </Paper>
      </Box>
    </Container>
  );
}
