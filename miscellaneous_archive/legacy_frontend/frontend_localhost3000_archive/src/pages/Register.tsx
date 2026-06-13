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
  Stepper,
  Step,
  StepLabel,
} from '@mui/material';
import PersonAddOutlinedIcon from '@mui/icons-material/PersonAddOutlined';
import { FormInput, PasswordInput, CheckboxInput, OTPInput } from '@/components/common';
import { useAuth } from '@/hooks/useAuth';
import { 
  registerSchema, 
  otpVerificationSchema,
  type RegisterFormData,
  type OTPVerificationFormData 
} from '@/features/auth/utils/validation';

type Step = 'register' | 'verify';

export function Register() {
  const navigate = useNavigate();
  const { register: registerUser, verifyEmail, resendOtp, isRegisterPending, isVerifyPending, error, clearError } = useAuth();
  const [currentStep, setCurrentStep] = useState<Step>('register');
  const [registeredEmail, setRegisteredEmail] = useState('');
  const [showError, setShowError] = useState(true);
  const [resendCooldown, setResendCooldown] = useState(0);

  // Register form
  const registerForm = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      email: '',
      username: '',
      password: '',
      confirmPassword: '',
      acceptTerms: false,
    },
  });

  // OTP form
  const otpForm = useForm<OTPVerificationFormData>({
    resolver: zodResolver(otpVerificationSchema),
    defaultValues: {
      email: '',
      otp: '',
    },
  });

  const onRegisterSubmit = async (data: RegisterFormData) => {
    try {
      setShowError(true);
      clearError();
      await registerUser(data);
      setRegisteredEmail(data.email);
      otpForm.setValue('email', data.email);
      setCurrentStep('verify');
    } catch (err) {
      console.error('Registration error:', err);
    }
  };

  const onVerifySubmit = async (data: OTPVerificationFormData) => {
    try {
      setShowError(true);
      clearError();
      await verifyEmail(data);
      navigate('/dashboard');
    } catch (err) {
      console.error('Verification error:', err);
    }
  };

  const handleResendOtp = async () => {
    if (resendCooldown > 0) return;

    try {
      await resendOtp(registeredEmail);
      setResendCooldown(60);
      const interval = setInterval(() => {
        setResendCooldown((prev) => {
          if (prev <= 1) {
            clearInterval(interval);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } catch (err) {
      console.error('Resend OTP error:', err);
    }
  };

  const steps = ['Create Account', 'Verify Email'];
  const activeStep = currentStep === 'register' ? 0 : 1;

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
              <PersonAddOutlinedIcon sx={{ color: 'white', fontSize: 28 }} />
            </Box>
            <Typography variant="h4" component="h1" fontWeight={600}>
              Sign Up
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Create your ML Trading Signals account
            </Typography>
          </Box>

          {/* Stepper */}
          <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>

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

          {/* Register Step */}
          {currentStep === 'register' && (
            <Box component="form" onSubmit={registerForm.handleSubmit(onRegisterSubmit)} noValidate>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
                <FormInput
                  name="email"
                  control={registerForm.control}
                  label="Email Address"
                  type="email"
                  placeholder="you@example.com"
                  autoComplete="email"
                  disabled={isRegisterPending}
                />

                <FormInput
                  name="username"
                  control={registerForm.control}
                  label="Username"
                  placeholder="johndoe"
                  autoComplete="username"
                  disabled={isRegisterPending}
                />

                <PasswordInput
                  name="password"
                  control={registerForm.control}
                  label="Password"
                  placeholder="Create a strong password"
                  autoComplete="new-password"
                  showStrength
                  disabled={isRegisterPending}
                />

                <PasswordInput
                  name="confirmPassword"
                  control={registerForm.control}
                  label="Confirm Password"
                  placeholder="Re-enter your password"
                  autoComplete="new-password"
                  disabled={isRegisterPending}
                />

                <CheckboxInput
                  name="acceptTerms"
                  control={registerForm.control}
                  label={
                    <Typography variant="body2">
                      I agree to the{' '}
                      <Link href="#" underline="hover">
                        Terms & Conditions
                      </Link>{' '}
                      and{' '}
                      <Link href="#" underline="hover">
                        Privacy Policy
                      </Link>
                    </Typography>
                  }
                  disabled={isRegisterPending}
                />

                <Button
                  type="submit"
                  variant="contained"
                  size="large"
                  fullWidth
                  disabled={isRegisterPending}
                  sx={{ mt: 1, py: 1.5 }}
                >
                  {isRegisterPending ? (
                    <>
                      <CircularProgress size={20} sx={{ mr: 1 }} />
                      Creating Account...
                    </>
                  ) : (
                    'Create Account'
                  )}
                </Button>
              </Box>
            </Box>
          )}

          {/* OTP Verification Step */}
          {currentStep === 'verify' && (
            <Box>
              <Typography variant="body1" textAlign="center" gutterBottom>
                We've sent a verification code to
              </Typography>
              <Typography variant="body1" fontWeight={600} textAlign="center" sx={{ mb: 3 }}>
                {registeredEmail}
              </Typography>

              <Box component="form" onSubmit={otpForm.handleSubmit(onVerifySubmit)} noValidate>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                  <OTPInput
                    name="otp"
                    control={otpForm.control}
                    length={6}
                    disabled={isVerifyPending}
                    onComplete={(otp) => {
                      otpForm.setValue('otp', otp);
                      otpForm.handleSubmit(onVerifySubmit)();
                    }}
                  />

                  <Button
                    type="submit"
                    variant="contained"
                    size="large"
                    fullWidth
                    disabled={isVerifyPending}
                    sx={{ py: 1.5 }}
                  >
                    {isVerifyPending ? (
                      <>
                        <CircularProgress size={20} sx={{ mr: 1 }} />
                        Verifying...
                      </>
                    ) : (
                      'Verify Email'
                    )}
                  </Button>

                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="body2" color="text.secondary">
                      Didn't receive the code?{' '}
                      <Link
                        component="button"
                        type="button"
                        variant="body2"
                        underline="hover"
                        fontWeight={600}
                        onClick={handleResendOtp}
                        disabled={resendCooldown > 0}
                        sx={{ cursor: resendCooldown > 0 ? 'not-allowed' : 'pointer' }}
                      >
                        {resendCooldown > 0 ? `Resend in ${resendCooldown}s` : 'Resend OTP'}
                      </Link>
                    </Typography>
                  </Box>
                </Box>
              </Box>
            </Box>
          )}

          <Divider sx={{ my: 3 }}>
            <Typography variant="body2" color="text.secondary">
              OR
            </Typography>
          </Divider>

          {/* Login Link */}
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              Already have an account?{' '}
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
        </Paper>
      </Box>
    </Container>
  );
}
