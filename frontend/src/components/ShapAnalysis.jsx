import React, { useState, useEffect } from 'react';
import { 
  Box, Grid, Card, CardContent, Typography, CircularProgress, 
  Alert, LinearProgress
} from '@mui/material';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, 
  Legend, ResponsiveContainer, Cell
} from 'recharts';
import InfoIcon from '@mui/icons-material/Info';
import ExportButtons from './ExportButtons';
import axios from '../utils/axios';

function ShapAnalysis() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [imageUrl, setImageUrl] = useState(null);

  useEffect(() => {
    fetchShapData();
    setImageUrl(`http://localhost:5000/api/shap/plot?t=${Date.now()}`);
  }, []);

  const fetchShapData = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`/shap/feature-importance`);
      setData(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to load SHAP analysis.');
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
      <Alert severity="info" sx={{ mb: 3 }}>
        {error}
        <br /><br />
        <strong>To generate SHAP analysis:</strong><br />
        <code>python run.py --mode explain</code>
      </Alert>
    );
  }

  const featureData = data?.feature_importance || [];
  
  // Sort by importance
  const sortedFeatures = [...featureData].sort((a, b) => b.importance - a.importance);
  
  // Color scale for bars
  const getColor = (index) => {
    const colors = ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#43e97b'];
    return colors[index % colors.length];
  };

  return (
    <Box>
      {/* Export Buttons */}
      <ExportButtons data={data} type="shap" filename="ml_signals_shap" />
      
      {/* Info Card */}
      <Alert severity="info" icon={<InfoIcon />} sx={{ mb: 4 }}>
        <Typography variant="body2" fontWeight="600" mb={1}>
          What is SHAP?
        </Typography>
        <Typography variant="body2">
          SHAP (SHapley Additive exPlanations) reveals which features drive model predictions. 
          Higher values indicate stronger influence on the model's decision to generate trading signals.
        </Typography>
      </Alert>

      {/* Top Features Summary */}
      <Card className="stat-card" sx={{ mb: 4, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
        <CardContent>
          <Typography variant="h6" fontWeight="600" mb={2}>
            🏆 Top 3 Most Important Features
          </Typography>
          <Grid container spacing={3}>
            {sortedFeatures.slice(0, 3).map((feature, idx) => (
              <Grid item xs={12} md={4} key={idx}>
                <Box sx={{ background: 'rgba(255,255,255,0.1)', borderRadius: 2, p: 2 }}>
                  <Typography variant="h4" fontWeight="700" mb={1}>
                    #{idx + 1}
                  </Typography>
                  <Typography variant="body1" fontWeight="600" mb={1}>
                    {feature.feature.replace(/_/g, ' ').toUpperCase()}
                  </Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={feature.importance * 100} 
                    sx={{ 
                      height: 8, 
                      borderRadius: 4,
                      bgcolor: 'rgba(255,255,255,0.2)',
                      '& .MuiLinearProgress-bar': {
                        bgcolor: 'white'
                      }
                    }}
                  />
                  <Typography variant="body2" sx={{ mt: 1, opacity: 0.9 }}>
                    Impact: {(feature.importance * 100).toFixed(1)}%
                  </Typography>
                </Box>
              </Grid>
            ))}
          </Grid>
        </CardContent>
      </Card>

      {/* Feature Importance Chart */}
      <Card className="stat-card" sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom fontWeight="600">
            📊 Feature Importance Rankings
          </Typography>
          <Typography variant="body2" color="text.secondary" mb={3}>
            All features ranked by their contribution to model predictions
          </Typography>
          
          <ResponsiveContainer width="100%" height={500}>
            <BarChart 
              data={sortedFeatures} 
              layout="vertical"
              margin={{ top: 5, right: 30, left: 150, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis 
                type="number" 
                stroke="#666"
                tickFormatter={(val) => `${(val * 100).toFixed(0)}%`}
              />
              <YAxis 
                type="category" 
                dataKey="feature" 
                stroke="#666"
                tick={{ fontSize: 12 }}
                width={140}
              />
              <Tooltip 
                formatter={(value) => [`${(value * 100).toFixed(2)}%`, 'Importance']}
                contentStyle={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: 8 }}
              />
              
              <Bar dataKey="importance" radius={[0, 8, 8, 0]}>
                {sortedFeatures.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={getColor(index)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Feature Details */}
      <Card className="stat-card" sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom fontWeight="600">
            📋 Feature Details
          </Typography>
          
          <Box sx={{ mt: 3 }}>
            {sortedFeatures.map((feature, idx) => (
              <Box 
                key={idx}
                sx={{ 
                  p: 2, 
                  mb: 2, 
                  background: idx < 3 ? '#f0f9ff' : '#f9fafb', 
                  borderRadius: 2,
                  borderLeft: idx < 3 ? '4px solid #667eea' : '4px solid #e5e7eb'
                }}
              >
                <Grid container spacing={2} alignItems="center">
                  <Grid item xs={1}>
                    <Typography variant="h6" fontWeight="700" color={idx < 3 ? 'primary' : 'text.secondary'}>
                      #{idx + 1}
                    </Typography>
                  </Grid>
                  <Grid item xs={5}>
                    <Typography variant="body1" fontWeight="600">
                      {feature.feature.replace(/_/g, ' ')}
                    </Typography>
                  </Grid>
                  <Grid item xs={4}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <LinearProgress 
                        variant="determinate" 
                        value={feature.importance * 100} 
                        sx={{ 
                          flexGrow: 1, 
                          height: 10, 
                          borderRadius: 4,
                          bgcolor: '#e5e7eb'
                        }}
                      />
                    </Box>
                  </Grid>
                  <Grid item xs={2}>
                    <Typography variant="body1" fontWeight="700" color="primary">
                      {(feature.importance * 100).toFixed(1)}%
                    </Typography>
                  </Grid>
                </Grid>
              </Box>
            ))}
          </Box>
        </CardContent>
      </Card>

      {/* SHAP Summary Plot (if available) */}
      {imageUrl && (
        <Card className="stat-card">
          <CardContent>
            <Typography variant="h6" gutterBottom fontWeight="600">
              🎨 SHAP Summary Plot
            </Typography>
            <Typography variant="body2" color="text.secondary" mb={3}>
              Visual representation of feature impacts on model predictions
            </Typography>
            
            <Box 
              sx={{ 
                display: 'flex', 
                justifyContent: 'center', 
                alignItems: 'center',
                background: '#f9fafb',
                borderRadius: 2,
                p: 3,
                minHeight: 400
              }}
            >
              <img 
                src={imageUrl} 
                alt="SHAP Feature Importance" 
                style={{ 
                  maxWidth: '100%', 
                  height: 'auto',
                  borderRadius: 8
                }}
                onError={(e) => {
                  e.target.style.display = 'none';
                  e.target.parentElement.innerHTML = '<p style="color: #6b7280;">SHAP plot not available. Run: python run.py --mode explain</p>';
                }}
              />
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Feature Categories */}
      <Card className="stat-card" sx={{ mt: 4 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom fontWeight="600">
            🏷️ Feature Categories
          </Typography>
          
          <Grid container spacing={3} sx={{ mt: 2 }}>
            <Grid item xs={12} md={4}>
              <Box sx={{ p: 3, background: '#f0f9ff', borderRadius: 2 }}>
                <Typography variant="subtitle1" fontWeight="600" color="primary" mb={2}>
                  📊 Volume Features
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  volume_imbalance, order_flow, volume_spike
                </Typography>
              </Box>
            </Grid>
            
            <Grid item xs={12} md={4}>
              <Box sx={{ p: 3, background: '#f0fdf4', borderRadius: 2 }}>
                <Typography variant="subtitle1" fontWeight="600" color="success.main" mb={2}>
                  📈 Price Action Features
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  vwap_distance, trend_strength, volatility
                </Typography>
              </Box>
            </Grid>
            
            <Grid item xs={12} md={4}>
              <Box sx={{ p: 3, background: '#fef3c7', borderRadius: 2 }}>
                <Typography variant="subtitle1" fontWeight="600" sx={{ color: '#f59e0b' }} mb={2}>
                  🎯 SMC Features
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  fvg_score, liquidity_sweep, smc_signal
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>
    </Box>
  );
}

export default ShapAnalysis;
