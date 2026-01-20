import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Slider,
  Button,
  Grid,
  Alert,
  Divider
} from '@mui/material';
import SettingsIcon from '@mui/icons-material/Settings';
import SaveIcon from '@mui/icons-material/Save';
import RestartAltIcon from '@mui/icons-material/RestartAlt';

function ConfigurationPanel({ onConfigChange }) {
  const [config, setConfig] = useState({
    commodity: 'XAUUSD',
    timeframe: '15m',
    tpSlRatio: 3.0,
    signalThreshold: 0.5,
    sessionFilter: true
  });

  const [saved, setSaved] = useState(false);

  const handleChange = (field, value) => {
    setConfig(prev => ({ ...prev, [field]: value }));
    setSaved(false);
  };

  const handleSave = () => {
    if (onConfigChange) {
      onConfigChange(config);
    }
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  const handleReset = () => {
    setConfig({
      commodity: 'XAUUSD',
      timeframe: '15m',
      tpSlRatio: 3.0,
      signalThreshold: 0.5,
      sessionFilter: true
    });
    setSaved(false);
  };

  return (
    <Box>
      {saved && (
        <Alert severity="success" sx={{ mb: 3 }}>
          Configuration saved successfully! Changes will apply on next prediction.
        </Alert>
      )}

      <Card className="stat-card" sx={{ mb: 4 }}>
        <CardContent>
          <Box display="flex" alignItems="center" mb={3}>
            <SettingsIcon sx={{ mr: 1, color: '#667eea', fontSize: 28 }} />
            <Typography variant="h5" fontWeight="600">
              Forecasting Configuration
            </Typography>
          </Box>

          <Typography variant="body2" color="text.secondary" mb={4}>
            Customize your prediction settings for analysis
          </Typography>

          <Grid container spacing={4}>
            {/* Commodity Selection */}
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Commodity</InputLabel>
                <Select
                  value={config.commodity}
                  label="Commodity"
                  onChange={(e) => handleChange('commodity', e.target.value)}
                >
                  <MenuItem value="XAUUSD">Gold (XAU/USD)</MenuItem>
                  <MenuItem value="XAGUSD">Silver (XAG/USD)</MenuItem>
                </Select>
              </FormControl>
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                Select the precious metal to analyze
              </Typography>
            </Grid>

            {/* Timeframe Selection */}
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Timeframe</InputLabel>
                <Select
                  value={config.timeframe}
                  label="Timeframe"
                  onChange={(e) => handleChange('timeframe', e.target.value)}
                >
                  <MenuItem value="5m">5 Minutes</MenuItem>
                  <MenuItem value="15m">15 Minutes (Recommended)</MenuItem>
                  <MenuItem value="30m">30 Minutes</MenuItem>
                  <MenuItem value="1h">1 Hour</MenuItem>
                </Select>
              </FormControl>
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                Primary timeframe for predictions
              </Typography>
            </Grid>

            <Grid item xs={12}>
              <Divider sx={{ my: 2 }} />
            </Grid>

            {/* TP/SL Ratio Slider */}
            <Grid item xs={12}>
              <Typography gutterBottom fontWeight="500">
                Take Profit / Stop Loss Ratio: {config.tpSlRatio.toFixed(1)}:1
              </Typography>
              <Slider
                value={config.tpSlRatio}
                onChange={(e, value) => handleChange('tpSlRatio', value)}
                min={1.5}
                max={5.0}
                step={0.5}
                marks={[
                  { value: 1.5, label: '1.5:1' },
                  { value: 3.0, label: '3:1' },
                  { value: 5.0, label: '5:1' }
                ]}
                valueLabelDisplay="auto"
                sx={{
                  '& .MuiSlider-thumb': {
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                  },
                  '& .MuiSlider-track': {
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                  }
                }}
              />
              <Typography variant="caption" color="text.secondary">
                Risk/reward ratio for trade exits. Higher values = more aggressive profit targets.
              </Typography>
            </Grid>

            {/* Signal Threshold Slider */}
            <Grid item xs={12}>
              <Typography gutterBottom fontWeight="500">
                Signal Threshold: {(config.signalThreshold * 100).toFixed(0)}%
              </Typography>
              <Slider
                value={config.signalThreshold}
                onChange={(e, value) => handleChange('signalThreshold', value)}
                min={0.3}
                max={0.8}
                step={0.05}
                marks={[
                  { value: 0.3, label: '30%' },
                  { value: 0.5, label: '50%' },
                  { value: 0.8, label: '80%' }
                ]}
                valueLabelDisplay="auto"
                valueLabelFormat={(value) => `${(value * 100).toFixed(0)}%`}
                sx={{
                  '& .MuiSlider-thumb': {
                    background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)'
                  },
                  '& .MuiSlider-track': {
                    background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)'
                  }
                }}
              />
              <Typography variant="caption" color="text.secondary">
                Minimum confidence required to generate a signal. Higher = fewer but stronger signals.
              </Typography>
            </Grid>

            {/* Session Filter */}
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Session Filter</InputLabel>
                <Select
                  value={config.sessionFilter}
                  label="Session Filter"
                  onChange={(e) => handleChange('sessionFilter', e.target.value)}
                >
                  <MenuItem value={true}>London + NY Overlap (8:00 - 17:00)</MenuItem>
                  <MenuItem value={false}>All Sessions (24/7)</MenuItem>
                </Select>
              </FormControl>
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                Filter predictions to high-volume trading sessions
              </Typography>
            </Grid>
          </Grid>

          {/* Action Buttons */}
          <Box sx={{ mt: 4, display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
            <Button
              variant="outlined"
              startIcon={<RestartAltIcon />}
              onClick={handleReset}
              sx={{ borderColor: '#667eea', color: '#667eea' }}
            >
              Reset to Default
            </Button>
            <Button
              variant="contained"
              startIcon={<SaveIcon />}
              onClick={handleSave}
              sx={{
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                '&:hover': {
                  background: 'linear-gradient(135deg, #5568d3 0%, #6a3f8f 100%)'
                }
              }}
            >
              Save Configuration
            </Button>
          </Box>
        </CardContent>
      </Card>

      {/* Current Configuration Summary */}
      <Card className="stat-card">
        <CardContent>
          <Typography variant="h6" fontWeight="600" gutterBottom>
            📋 Current Configuration
          </Typography>
          <Grid container spacing={2} sx={{ mt: 2 }}>
            <Grid item xs={6} md={3}>
              <Typography variant="body2" color="text.secondary">
                Commodity
              </Typography>
              <Typography variant="body1" fontWeight="600">
                {config.commodity === 'XAUUSD' ? 'Gold (XAU/USD)' : 'Silver (XAG/USD)'}
              </Typography>
            </Grid>
            <Grid item xs={6} md={3}>
              <Typography variant="body2" color="text.secondary">
                Timeframe
              </Typography>
              <Typography variant="body1" fontWeight="600">
                {config.timeframe}
              </Typography>
            </Grid>
            <Grid item xs={6} md={3}>
              <Typography variant="body2" color="text.secondary">
                TP/SL Ratio
              </Typography>
              <Typography variant="body1" fontWeight="600">
                {config.tpSlRatio.toFixed(1)}:1
              </Typography>
            </Grid>
            <Grid item xs={6} md={3}>
              <Typography variant="body2" color="text.secondary">
                Signal Threshold
              </Typography>
              <Typography variant="body1" fontWeight="600">
                {(config.signalThreshold * 100).toFixed(0)}%
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>
    </Box>
  );
}

export default ConfigurationPanel;
