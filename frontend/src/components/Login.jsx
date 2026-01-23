import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Alert,
  CircularProgress,
  Container,
  Link,
  Divider
} from '@mui/material';
import LockOutlinedIcon from '@mui/icons-material/LockOutlined';
import axios from 'axios';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const API_BASE = 'http://localhost:5000/api';

function Login({ onLoginSuccess }) {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const endpoint = isLogin ? '/auth/login' : '/auth/register';
      const response = await axios.post(`${API_BASE}${endpoint}`, {
        email,
        password
      });

      if (isLogin) {
        // Login successful - store token
        localStorage.setItem('token', response.data.token);
        localStorage.setItem('user_email', email);
        
        // Show success toast
        toast.success(`🎉 Welcome back, ${email}!`, {
          position: "top-center",
          autoClose: 2000,
          hideProgressBar: false,
          closeOnClick: true,
          pauseOnHover: true,
          draggable: true,
        });
        
        // Delay to show toast before redirecting
        setTimeout(() => {
          if (onLoginSuccess) {
            onLoginSuccess(response.data.token, email);
          }
        }, 1000);
      } else {
        // Registration successful
        toast.success('✅ Account created successfully! Please login.', {
          position: "top-center",
          autoClose: 3000,
        });
        setIsLogin(true);
        setPassword('');
      }
    } catch (err) {
      const errorMsg = err.response?.data?.error || err.message || 'An error occurred';
      setError(errorMsg);
      
      // Show error toast
      toast.error(`❌ ${errorMsg}`, {
        position: "top-center",
        autoClose: 4000,
      });
    } finally {
      setLoading(false);
    }
  };

  const toggleMode = () => {
    setIsLogin(!isLogin);
    setError(null);
    setSuccess(null);
    setPassword('');
  };

  return (
    <>
      <ToastContainer />
      <Container maxWidth="sm">
        <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        }}
      >
        <Card sx={{ width: '100%', maxWidth: 450 }}>
          <CardContent sx={{ p: 4 }}>
            {/* Header */}
            <Box sx={{ textAlign: 'center', mb: 3 }}>
              <Box
                sx={{
                  width: 60,
                  height: 60,
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  margin: '0 auto',
                  mb: 2
                }}
              >
                <LockOutlinedIcon sx={{ fontSize: 30, color: 'white' }} />
              </Box>
              <Typography variant="h4" fontWeight="700" gutterBottom>
                MetalMind SMC
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {isLogin ? 'Sign in to access predictions' : 'Create your account'}
              </Typography>
            </Box>

            {/* Error Alert */}
            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}

            {/* Success Alert */}
            {success && (
              <Alert severity="success" sx={{ mb: 2 }}>
                {success}
              </Alert>
            )}

            {/* Form */}
            <form onSubmit={handleSubmit}>
              <TextField
                fullWidth
                label="Email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                sx={{ mb: 2 }}
                disabled={loading}
              />

              <TextField
                fullWidth
                label="Password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                sx={{ mb: 3 }}
                disabled={loading}
                helperText={!isLogin && "Minimum 8 characters, 1 uppercase, 1 number, 1 special char"}
              />

              <Button
                fullWidth
                variant="contained"
                type="submit"
                size="large"
                disabled={loading}
                sx={{
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  py: 1.5,
                  fontSize: '1rem',
                  fontWeight: 600,
                  textTransform: 'none',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #5568d3 0%, #6a3f8f 100%)',
                  }
                }}
              >
                {loading ? (
                  <CircularProgress size={24} sx={{ color: 'white' }} />
                ) : (
                  isLogin ? 'Sign In' : 'Create Account'
                )}
              </Button>
            </form>

            {/* Toggle between login/register */}
            <Divider sx={{ my: 3 }} />

            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="body2" color="text.secondary">
                {isLogin ? "Don't have an account? " : "Already have an account? "}
                <Link
                  component="button"
                  variant="body2"
                  onClick={toggleMode}
                  sx={{ fontWeight: 600, cursor: 'pointer' }}
                >
                  {isLogin ? 'Sign Up' : 'Sign In'}
                </Link>
              </Typography>
            </Box>

            {/* Demo Credentials (for testing) */}
            <Box sx={{ mt: 3, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
              <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
                <strong>Demo Account:</strong>
              </Typography>
              <Typography variant="caption" color="text.secondary" display="block">
                Email: demo@metalmind.com
              </Typography>
              <Typography variant="caption" color="text.secondary" display="block">
                Password: Demo123!@#
              </Typography>
            </Box>
          </CardContent>
        </Card>
      </Box>
    </Container>
    </>
  );
}

export default Login;
