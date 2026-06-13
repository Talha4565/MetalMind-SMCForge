import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import {
  Box,
  Container,
  Typography,
  Paper,
  Button,
  Grid,
  Divider,
  Alert,
  CircularProgress,
  Chip,
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CancelIcon from '@mui/icons-material/Cancel';
import { FormInput, PasswordInput } from '@/components/common';
import { useAuthStore } from '@/features/auth/store/authStore';
import { changePasswordSchema, type ChangePasswordFormData } from '@/features/auth/utils/validation';
import { apiClient, handleApiError } from '@/api/client';
import { API_ENDPOINTS } from '@/config/constants';
import { toast } from 'react-toastify';

export function Profile() {
  const user = useAuthStore((state) => state.user);
  const updateUser = useAuthStore((state) => state.updateUser);
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { control, handleSubmit, reset } = useForm<ChangePasswordFormData>({
    resolver: zodResolver(changePasswordSchema),
    defaultValues: {
      currentPassword: '',
      newPassword: '',
      confirmPassword: '',
    },
  });

  const onPasswordSubmit = async (data: ChangePasswordFormData) => {
    try {
      setIsChangingPassword(true);
      setError(null);

      await apiClient.put(API_ENDPOINTS.changePassword, {
        currentPassword: data.currentPassword,
        newPassword: data.newPassword,
      });

      toast.success('Password changed successfully');
      reset();
    } catch (err) {
      const message = handleApiError(err);
      setError(message);
      toast.error(message);
    } finally {
      setIsChangingPassword(false);
    }
  };

  if (!user) {
    return null;
  }

  return (
    <Container maxWidth="md">
      <Box sx={{ py: 4 }}>
        <Typography variant="h3" gutterBottom>
          Profile Settings
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          Manage your account information and security settings
        </Typography>

        {/* Account Information */}
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h5" gutterBottom>
            Account Information
          </Typography>
          <Divider sx={{ mb: 3 }} />

          <Grid container spacing={3}>
            <Grid item xs={12} sm={6}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Username
              </Typography>
              <Typography variant="body1" fontWeight={500}>
                {user.username}
              </Typography>
            </Grid>

            <Grid item xs={12} sm={6}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Email Address
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="body1" fontWeight={500}>
                  {user.email}
                </Typography>
                {user.verified ? (
                  <Chip
                    icon={<CheckCircleIcon />}
                    label="Verified"
                    color="success"
                    size="small"
                  />
                ) : (
                  <Chip
                    icon={<CancelIcon />}
                    label="Not Verified"
                    color="error"
                    size="small"
                  />
                )}
              </Box>
            </Grid>

            <Grid item xs={12} sm={6}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Account Created
              </Typography>
              <Typography variant="body1" fontWeight={500}>
                {new Date(user.createdAt).toLocaleDateString()}
              </Typography>
            </Grid>

            {user.lastLogin && (
              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Last Login
                </Typography>
                <Typography variant="body1" fontWeight={500}>
                  {new Date(user.lastLogin).toLocaleString()}
                </Typography>
              </Grid>
            )}
          </Grid>
        </Paper>

        {/* Change Password */}
        <Paper sx={{ p: 3 }}>
          <Typography variant="h5" gutterBottom>
            Change Password
          </Typography>
          <Divider sx={{ mb: 3 }} />

          {error && (
            <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          <Box component="form" onSubmit={handleSubmit(onPasswordSubmit)} noValidate>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
              <PasswordInput
                name="currentPassword"
                control={control}
                label="Current Password"
                autoComplete="current-password"
                disabled={isChangingPassword}
              />

              <PasswordInput
                name="newPassword"
                control={control}
                label="New Password"
                autoComplete="new-password"
                showStrength
                disabled={isChangingPassword}
              />

              <PasswordInput
                name="confirmPassword"
                control={control}
                label="Confirm New Password"
                autoComplete="new-password"
                disabled={isChangingPassword}
              />

              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end', mt: 1 }}>
                <Button
                  variant="outlined"
                  onClick={() => reset()}
                  disabled={isChangingPassword}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="contained"
                  disabled={isChangingPassword}
                >
                  {isChangingPassword ? (
                    <>
                      <CircularProgress size={20} sx={{ mr: 1 }} />
                      Changing...
                    </>
                  ) : (
                    'Change Password'
                  )}
                </Button>
              </Box>
            </Box>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
}
