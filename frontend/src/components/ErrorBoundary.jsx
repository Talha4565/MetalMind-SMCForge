import React from 'react';
import { Box, Typography, Button, Card, CardContent, Alert } from '@mui/material';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { 
      hasError: false, 
      error: null,
      errorInfo: null 
    };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Log error details for debugging
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    
    this.setState({
      error: error,
      errorInfo: errorInfo
    });
  }

  handleReload = () => {
    window.location.reload();
  };

  handleGoHome = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <Box
          sx={{
            minHeight: '100vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            p: 3
          }}
        >
          <Card sx={{ maxWidth: 600, width: '100%' }}>
            <CardContent sx={{ p: 4, textAlign: 'center' }}>
              {/* Icon */}
              <Box
                sx={{
                  width: 80,
                  height: 80,
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  margin: '0 auto',
                  mb: 3
                }}
              >
                <ErrorOutlineIcon sx={{ fontSize: 48, color: 'white' }} />
              </Box>

              {/* Title */}
              <Typography variant="h4" fontWeight="700" gutterBottom color="error">
                Oops! Something went wrong
              </Typography>

              {/* Description */}
              <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
                The application encountered an unexpected error. 
                Don't worry, your data is safe.
              </Typography>

              {/* Error Details (in development) */}
              {process.env.NODE_ENV === 'development' && this.state.error && (
                <Alert severity="error" sx={{ mb: 3, textAlign: 'left' }}>
                  <Typography variant="body2" fontWeight="600" gutterBottom>
                    Error Details:
                  </Typography>
                  <Typography variant="caption" component="pre" sx={{ fontSize: '0.75rem', whiteSpace: 'pre-wrap' }}>
                    {this.state.error.toString()}
                  </Typography>
                  {this.state.errorInfo && (
                    <Typography variant="caption" component="pre" sx={{ fontSize: '0.7rem', mt: 1, whiteSpace: 'pre-wrap' }}>
                      {this.state.errorInfo.componentStack}
                    </Typography>
                  )}
                </Alert>
              )}

              {/* Action Buttons */}
              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
                <Button
                  variant="contained"
                  size="large"
                  onClick={this.handleReload}
                  sx={{
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    px: 4,
                    '&:hover': {
                      background: 'linear-gradient(135deg, #5568d3 0%, #6a3f8f 100%)',
                    }
                  }}
                >
                  Reload Page
                </Button>

                <Button
                  variant="outlined"
                  size="large"
                  onClick={this.handleGoHome}
                  sx={{
                    borderColor: '#667eea',
                    color: '#667eea',
                    px: 4,
                    '&:hover': {
                      borderColor: '#5568d3',
                      backgroundColor: 'rgba(102, 126, 234, 0.04)',
                    }
                  }}
                >
                  Try Again
                </Button>
              </Box>

              {/* Help Text */}
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 3 }}>
                If this problem persists, please contact support or check the browser console for more details.
              </Typography>
            </CardContent>
          </Card>
        </Box>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
