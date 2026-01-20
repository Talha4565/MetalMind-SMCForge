import React, { useState, useEffect } from 'react';
import { 
  Box, Grid, Card, CardContent, Typography, CircularProgress, 
  Alert, Chip, LinearProgress 
} from '@mui/material';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, 
  Legend, ResponsiveContainer, ReferenceLine, Scatter, ComposedChart
} from 'recharts';
import axios from 'axios';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import ShowChartIcon from '@mui/icons-material/ShowChart';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';

const API_BASE = 'http://localhost:5000/api';

function LivePredictions() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchPredictions();
  }, []);

  const fetchPredictions = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE}/predictions/latest`);
      setData(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to load predictions. Make sure the API is running on port 5000.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress size={60} />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 3 }}>
        {error}
        <br /><br />
        <strong>To start the API:</strong><br />
        <code>cd ml-signals && python api/app/main.py</code>
      </Alert>
    );
  }

  const predictions = data?.predictions || [];
  const signals = predictions.filter(p => p.signal === 1);
  
  // Calculate signal density (signals per hour)
  const signalDensity = (signals.length / predictions.length) * 4; // 4 bars per hour (15m)

  return (
    <Box>
      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={3}>
          <Card className="stat-card" sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="body2" sx={{ opacity: 0.9, mb: 1 }}>
                    Model Accuracy
                  </Typography>
                  <Typography variant="h3" fontWeight="700">
                    {(data.model_accuracy * 100).toFixed(1)}%
                  </Typography>
                </Box>
                <CheckCircleIcon sx={{ fontSize: 48, opacity: 0.7 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card className="stat-card">
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="body2" color="text.secondary" mb={1}>
                    Total Signals
                  </Typography>
                  <Typography variant="h3" fontWeight="700" color="primary">
                    {data.total_signals}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Last 100 bars
                  </Typography>
                </Box>
                <TrendingUpIcon sx={{ fontSize: 48, color: '#667eea', opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card className="stat-card">
            <CardContent>
              <Typography variant="body2" color="text.secondary" mb={1}>
                Signal Density
              </Typography>
              <Typography variant="h3" fontWeight="700" color="success.main">
                {signalDensity.toFixed(1)}/hr
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Avg signals per hour
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card className="stat-card">
            <CardContent>
              <Typography variant="body2" color="text.secondary" mb={1}>
                Latest Price
              </Typography>
              <Typography variant="h3" fontWeight="700">
                ${predictions[predictions.length - 1]?.close.toFixed(2) || '-'}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                XAU/USD
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Price Chart with Signals */}
      <Card className="stat-card" sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom fontWeight="600">
            📊 Price Action with Trading Signals
          </Typography>
          <Typography variant="body2" color="text.secondary" mb={3}>
            Green markers indicate model predictions (signal = 1)
          </Typography>
          
          <ResponsiveContainer width="100%" height={400}>
            <ComposedChart data={predictions}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis 
                dataKey="timestamp" 
                tickFormatter={(val) => new Date(val).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                stroke="#666"
              />
              <YAxis 
                domain={['dataMin - 5', 'dataMax + 5']} 
                stroke="#666"
                tickFormatter={(val) => `$${val.toFixed(0)}`}
              />
              <Tooltip 
                formatter={(value, name) => {
                  if (name === 'close') return [`$${value.toFixed(2)}`, 'Close'];
                  if (name === 'probability') return [`${(value * 100).toFixed(1)}%`, 'Signal Probability'];
                  return [value, name];
                }}
                labelFormatter={(val) => new Date(val).toLocaleString()}
              />
              <Legend />
              
              <Line 
                type="monotone" 
                dataKey="close" 
                stroke="#667eea" 
                strokeWidth={2}
                dot={false}
                name="Close Price"
              />
              
              <Scatter 
                dataKey={(entry) => entry.signal === 1 ? entry.close : null}
                fill="#10b981"
                name="Trading Signal"
                shape="circle"
              />
            </ComposedChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Prediction Confidence */}
      <Card className="stat-card">
        <CardContent>
          <Typography variant="h6" gutterBottom fontWeight="600">
            🎯 Signal Probability Distribution
          </Typography>
          <Typography variant="body2" color="text.secondary" mb={3}>
            Model confidence for each prediction (higher = stronger signal)
          </Typography>
          
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={predictions}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis 
                dataKey="timestamp" 
                tickFormatter={(val) => new Date(val).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                stroke="#666"
              />
              <YAxis 
                domain={[0, 1]} 
                stroke="#666"
                tickFormatter={(val) => `${(val * 100).toFixed(0)}%`}
              />
              <Tooltip 
                formatter={(value) => [`${(value * 100).toFixed(2)}%`, 'Probability']}
                labelFormatter={(val) => new Date(val).toLocaleString()}
              />
              <Legend />
              
              <ReferenceLine y={0.5} stroke="#999" strokeDasharray="3 3" label="Threshold" />
              
              <Line 
                type="monotone" 
                dataKey="probability" 
                stroke="#f59e0b" 
                strokeWidth={2}
                dot={false}
                name="Signal Probability"
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Recent Signals Table */}
      {signals.length > 0 && (
        <Card className="stat-card" sx={{ mt: 4 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom fontWeight="600">
              🔔 Recent Signals (Last {Math.min(10, signals.length)})
            </Typography>
            
            <Box sx={{ mt: 2 }}>
              {signals.slice(-10).reverse().map((signal, idx) => (
                <Box 
                  key={idx}
                  sx={{ 
                    p: 2, 
                    mb: 2, 
                    background: '#f9fafb', 
                    borderRadius: 2,
                    borderLeft: '4px solid #10b981'
                  }}
                >
                  <Grid container spacing={2} alignItems="center">
                    <Grid item xs={12} sm={3}>
                      <Typography variant="body2" color="text.secondary">
                        Time
                      </Typography>
                      <Typography variant="body1" fontWeight="600">
                        {new Date(signal.timestamp).toLocaleString()}
                      </Typography>
                    </Grid>
                    <Grid item xs={12} sm={2}>
                      <Typography variant="body2" color="text.secondary">
                        Price
                      </Typography>
                      <Typography variant="body1" fontWeight="600">
                        ${signal.close.toFixed(2)}
                      </Typography>
                    </Grid>
                    <Grid item xs={12} sm={3}>
                      <Typography variant="body2" color="text.secondary">
                        Confidence
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <LinearProgress 
                          variant="determinate" 
                          value={signal.probability * 100} 
                          sx={{ flexGrow: 1, height: 8, borderRadius: 4 }}
                        />
                        <Typography variant="body2" fontWeight="600">
                          {(signal.probability * 100).toFixed(0)}%
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={12} sm={4}>
                      <Chip 
                        label="LONG SIGNAL" 
                        color="success" 
                        size="small"
                        icon={<TrendingUpIcon />}
                      />
                    </Grid>
                  </Grid>
                </Box>
              ))}
            </Box>
          </CardContent>
        </Card>
      )}
    </Box>
  );
}

export default LivePredictions;
