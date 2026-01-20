import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  LinearProgress,
  Alert,
  Chip
} from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import DateRangeIcon from '@mui/icons-material/DateRange';
import axios from 'axios';

const API_BASE = 'http://localhost:5000/api';

function BacktestControl({ onBacktestComplete }) {
  const [config, setConfig] = useState({
    startDate: '2023-01-01',
    endDate: '2024-09-20',
    preset: 'all'
  });
  
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const presets = {
    'last_month': { label: 'Last Month', days: 30 },
    'last_3months': { label: 'Last 3 Months', days: 90 },
    'last_6months': { label: 'Last 6 Months', days: 180 },
    'last_year': { label: 'Last Year', days: 365 },
    'all': { label: 'All Available Data', days: null }
  };

  const handlePresetChange = (preset) => {
    setConfig(prev => ({ ...prev, preset }));
    
    if (preset === 'all') {
      setConfig(prev => ({
        ...prev,
        startDate: '2023-01-01',
        endDate: '2024-09-20'
      }));
    } else {
      const endDate = new Date('2024-09-20');
      const startDate = new Date(endDate);
      startDate.setDate(startDate.getDate() - presets[preset].days);
      
      setConfig(prev => ({
        ...prev,
        startDate: startDate.toISOString().split('T')[0],
        endDate: endDate.toISOString().split('T')[0]
      }));
    }
  };

  const runBacktest = async () => {
    setRunning(true);
    setProgress(0);
    setError(null);
    setResult(null);

    try {
      // Simulate progress (in real implementation, this would be WebSocket updates)
      const progressInterval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 90) return prev;
          return prev + 10;
        });
      }, 500);

      // Call API to run backtest
      const response = await axios.post(`${API_BASE}/backtest/run`, {
        start_date: config.startDate,
        end_date: config.endDate
      });

      clearInterval(progressInterval);
      setProgress(100);
      setResult(response.data);
      
      if (onBacktestComplete) {
        onBacktestComplete(response.data);
      }

      setTimeout(() => {
        setRunning(false);
      }, 1000);

    } catch (err) {
      setError('Backtest execution is currently command-line only. Use: python run.py --mode backtest');
      setRunning(false);
      setProgress(0);
      console.error('Backtest error:', err);
    }
  };

  return (
    <Card className="stat-card" sx={{ mb: 4 }}>
      <CardContent>
        <Box display="flex" alignItems="center" mb={3}>
          <DateRangeIcon sx={{ mr: 1, color: '#667eea', fontSize: 28 }} />
          <Typography variant="h5" fontWeight="600">
            Backtest Execution
          </Typography>
        </Box>

        <Typography variant="body2" color="text.secondary" mb={4}>
          Run historical backtests to evaluate strategy performance over different time periods
        </Typography>

        {error && (
          <Alert severity="info" sx={{ mb: 3 }}>
            {error}
            <br /><br />
            <strong>Current backtest results are from the last run.</strong> To regenerate with new parameters, use the command line.
          </Alert>
        )}

        {result && (
          <Alert severity="success" sx={{ mb: 3 }}>
            ✅ Backtest completed successfully! Total Return: <strong>+{result.summary?.total_return_pct.toFixed(2)}%</strong>
          </Alert>
        )}

        <Grid container spacing={3}>
          {/* Quick Presets */}
          <Grid item xs={12}>
            <Typography variant="subtitle2" gutterBottom fontWeight="600">
              Quick Presets
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
              {Object.entries(presets).map(([key, { label }]) => (
                <Chip
                  key={key}
                  label={label}
                  onClick={() => handlePresetChange(key)}
                  color={config.preset === key ? 'primary' : 'default'}
                  variant={config.preset === key ? 'filled' : 'outlined'}
                  sx={{
                    ...(config.preset === key && {
                      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                      color: 'white'
                    })
                  }}
                />
              ))}
            </Box>
          </Grid>

          {/* Date Range */}
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Start Date"
              type="date"
              value={config.startDate}
              onChange={(e) => setConfig(prev => ({ ...prev, startDate: e.target.value, preset: 'custom' }))}
              InputLabelProps={{ shrink: true }}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="End Date"
              type="date"
              value={config.endDate}
              onChange={(e) => setConfig(prev => ({ ...prev, endDate: e.target.value, preset: 'custom' }))}
              InputLabelProps={{ shrink: true }}
            />
          </Grid>

          {/* Progress Bar */}
          {running && (
            <Grid item xs={12}>
              <Box sx={{ width: '100%', mt: 2 }}>
                <Typography variant="body2" color="text.secondary" mb={1}>
                  Running backtest... {progress}%
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={progress}
                  sx={{
                    height: 10,
                    borderRadius: 5,
                    '& .MuiLinearProgress-bar': {
                      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                    }
                  }}
                />
              </Box>
            </Grid>
          )}

          {/* Run Button */}
          <Grid item xs={12}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Period: {config.startDate} to {config.endDate}
              </Typography>
              <Button
                variant="contained"
                size="large"
                startIcon={<PlayArrowIcon />}
                onClick={runBacktest}
                disabled={running}
                sx={{
                  background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                  px: 4,
                  '&:hover': {
                    background: 'linear-gradient(135deg, #059669 0%, #047857 100%)'
                  },
                  '&:disabled': {
                    background: '#e5e7eb'
                  }
                }}
              >
                {running ? 'Running...' : 'Run Backtest'}
              </Button>
            </Box>
          </Grid>
        </Grid>

        {/* Info Box */}
        <Box sx={{ mt: 4, p: 2, background: '#f0f9ff', borderRadius: 2, borderLeft: '4px solid #667eea' }}>
          <Typography variant="body2" fontWeight="600" mb={1}>
            ℹ️ How it works:
          </Typography>
          <Typography variant="body2" color="text.secondary">
            • Backtest runs the model on historical data within the selected period<br />
            • Uses walk-forward methodology to simulate realistic trading<br />
            • Applies current configuration settings (TP/SL ratio, signal threshold)<br />
            • Results appear in the "Backtest Results" tab after completion
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
}

export default BacktestControl;
