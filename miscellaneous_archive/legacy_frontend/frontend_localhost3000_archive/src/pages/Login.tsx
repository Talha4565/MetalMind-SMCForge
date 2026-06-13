import { useState } from 'react';
import { useNavigate, Link as RouterLink } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import {
  Box,
  Container,
  Typography,
  Paper,
  Button,
  Link,
  Divider,
  Alert,
  CircularProgress,
} from '@mui/material';
import LockOutlinedIcon from '@mui/icons-material/LockOutlined';
import { FormInput, PasswordInput, CheckboxInput } from '@/components/common';
import { useAuth } from '@/hooks/useAuth';
import { loginSchema, type LoginFormData } from '@/features/auth/utils/validation';

export function Login() {
  const navigate = useNavigate();
  const { login, isLoginPending, error, clearError } = useAuth();
  const [showError, setShowError] = useState(true);

  const {
    control,
    handleSubmit,
    formState: { isSubmitting },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
      rememberMe: false,
    },
  });

  const onSubmit = async (data: LoginFormData) => {
    try {
      setShowError(true);
      clearError();
      await login(data);
      navigate('/dashboard');
    } catch (err) {
      // Error is handled by useAuth hook
      console.error('Login error:', err);
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
              <LockOutlinedIcon sx={{ color: 'white', fontSize: 28 }} />
            </Box>
            <Typography variant="h4" component="h1" fontWeight={600}>
              Sign In
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Welcome back to ML Trading Signals
            </Typography>
          </Box>

          {/* Error Alert */}
          {error && showError && (
            <Alert
              severity="error"
              onClose={() => setShowError(false)}
              sx={{ mb: 3 }}
            >
              {error}
            </Alert>
          )}

          {/* Login Form */}
          <Box component="form" onSubmit={handleSubmit(onSubmit)} noValidate>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
              <FormInput
                name="email"
                control={control}
                label="Email Address"
                type="email"
                placeholder="you@example.com"
                autoComplete="email"
                disabled={isSubmitting || isLoginPending}
              />

              <PasswordInput
                name="password"
                control={control}
                label="Password"
                placeholder="Enter your password"
                autoComplete="current-password"
                disabled={isSubmitting || isLoginPending}
              />

              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <CheckboxInput
                  name="rememberMe"
                  control={control}
                  label="Remember me"
                  disabled={isSubmitting || isLoginPending}
                />
                <Link
                  component={RouterLink}
                  to="/forgot-password"
                  variant="body2"
                  underline="hover"
                  sx={{ fontWeight: 500 }}
                >
                  Forgot password?
                </Link>
              </Box>

              <Button
                type="submit"
                variant="contained"
                size="large"
                fullWidth
                disabled={isSubmitting || isLoginPending}
                sx={{ mt: 1, py: 1.5 }}
              >
                {isLoginPending ? (
                  <>
                    <CircularProgress size={20} sx={{ mr: 1 }} />
                    Signing in...
                  </>
                ) : (
                  'Sign In'
                )}
              </Button>
            </Box>
          </Box>

          <Divider sx={{ my: 3 }}>
            <Typography variant="body2" color="text.secondary">
              OR
            </Typography>
          </Divider>

          {/* Register Link */}
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              Don't have an account?{' '}
              <Link
                component={RouterLink}
                to="/register"
                variant="body2"
                underline="hover"
                fontWeight={600}
              >
                Sign up
              </Link>
            </Typography>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
}
