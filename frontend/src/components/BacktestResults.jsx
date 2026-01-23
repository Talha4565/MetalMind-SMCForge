import React, { useState, useEffect } from 'react';
import { 
  Box, Grid, Card, CardContent, Typography, CircularProgress, 
  Alert, Table, TableBody, TableCell, TableContainer, 
  TableHead, TableRow, Paper, Chip
} from '@mui/material';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, 
  Legend, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell
} from 'recharts';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import AccountBalanceIcon from '@mui/icons-material/AccountBalance';
import ShowChartIcon from '@mui/icons-material/ShowChart';
import ExportButtons from './ExportButtons';
import BacktestControl from './BacktestControl';
import axios from '../utils/axios';

function BacktestResults() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const handleBacktestComplete = (results) => {
    setData(results);
    setLoading(false);
    setError(null);
  };

  useEffect(() => {
    fetchBacktestResults();
  }, []);

  const fetchBacktestResults = async () => {
    try {
      setLoading(true);
      console.log('Fetching backtest results from API...');
      const response = await axios.get(`/backtest/results`);
      console.log('Backtest data received:', response.data);
      setData(response.data);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch backtest results:', err);
      setError('No backtest results found. Run: python run.py --mode backtest');
    } finally {
      setLoading(false);
    }
  };

  // Show loading only on initial load
  if (loading && !data) {
    return (
      <Box>
        <BacktestControl onBacktestComplete={handleBacktestComplete} />
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress size={60} />
        </Box>
      </Box>
    );
  }

  // Show error if fetch failed
  if (error && !data) {
    return (
      <Box>
        <BacktestControl onBacktestComplete={handleBacktestComplete} />
        <Alert severity="warning" sx={{ mb: 3 }}>
          {error}
        </Alert>
      </Box>
    );
  }

  // If no data after loading, show message
  if (!data || !data.summary || !data.trades) {
    return (
      <Box>
        <BacktestControl onBacktestComplete={handleBacktestComplete} />
        <Alert severity="info" sx={{ mt: 2 }}>
          No backtest results available. Click "Run Backtest" above to generate results.
        </Alert>
      </Box>
    );
  }

  const { summary, equity_curve = [], trades = [], session_performance = {} } = data;
  
  // Prepare session data for chart
  const sessionData = session_performance ? Object.entries(session_performance).map(([session, stats]) => ({
    session,
    trades: stats.trades,
    total_pnl: stats.total_pnl,
    win_rate: stats.win_rate * 100
  })) : [];

  // Win/Loss distribution
  const winLossData = [
    { name: 'Wins', value: Math.round(summary.win_rate * summary.n_trades), color: '#10b981' },
    { name: 'Losses', value: Math.round((1 - summary.win_rate) * summary.n_trades), color: '#ef4444' }
  ];

  return (
    <Box>
      {/* Backtest Control */}
      <BacktestControl onBacktestComplete={handleBacktestComplete} />
      
      {/* Export Buttons */}
      <ExportButtons data={data} type="backtest" filename="ml_signals_backtest" />
      
      {/* Summary Stats */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={3}>
          <Card className="stat-card" sx={{ background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)', color: 'white' }}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="body2" sx={{ opacity: 0.9, mb: 1 }}>
                    Total Return
                  </Typography>
                  <Typography variant="h3" fontWeight="700">
                    +{summary.total_return_pct.toFixed(1)}%
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9, mt: 1 }}>
                    ${summary.total_return_usd.toFixed(2)}
                  </Typography>
                </Box>
                <TrendingUpIcon sx={{ fontSize: 48, opacity: 0.7 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card className="stat-card">
            <CardContent>
              <Typography variant="body2" color="text.secondary" mb={1}>
                Win Rate
              </Typography>
              <Typography variant="h3" fontWeight="700" className="positive">
                {(summary.win_rate * 100).toFixed(1)}%
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {Math.round(summary.win_rate * summary.n_trades)} / {summary.n_trades} trades
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card className="stat-card">
            <CardContent>
              <Typography variant="body2" color="text.secondary" mb={1}>
                Profit Factor
              </Typography>
              <Typography variant="h3" fontWeight="700" color="primary">
                {summary.profit_factor.toFixed(2)}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Avg Win: ${summary.avg_win.toFixed(2)} | Loss: ${summary.avg_loss.toFixed(2)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card className="stat-card">
            <CardContent>
              <Typography variant="body2" color="text.secondary" mb={1}>
                Max Drawdown
              </Typography>
              <Typography variant="h3" fontWeight="700" className="negative">
                {summary.max_drawdown_pct.toFixed(2)}%
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Sharpe: {summary.sharpe_ratio.toFixed(2)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Equity Curve */}
      <Card className="stat-card" sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom fontWeight="600">
            💰 Equity Curve
          </Typography>
          <Typography variant="body2" color="text.secondary" mb={3}>
            Portfolio value over time
          </Typography>
          
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={equity_curve}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis 
                dataKey="timestamp" 
                tickFormatter={(val) => new Date(val).toLocaleDateString()}
                stroke="#666"
              />
              <YAxis 
                stroke="#666"
                tickFormatter={(val) => `$${val.toFixed(0)}`}
              />
              <Tooltip 
                formatter={(value) => [`$${value.toFixed(2)}`, 'Equity']}
                labelFormatter={(val) => new Date(val).toLocaleString()}
              />
              <Legend />
              
              <Line 
                type="monotone" 
                dataKey="equity" 
                stroke="#10b981" 
                strokeWidth={3}
                dot={false}
                name="Portfolio Value"
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Session Performance */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={6}>
          <Card className="stat-card">
            <CardContent>
              <Typography variant="h6" gutterBottom fontWeight="600">
                📊 Performance by Session
              </Typography>
              <Typography variant="body2" color="text.secondary" mb={3}>
                P&L breakdown by trading session
              </Typography>
              
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={sessionData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="session" stroke="#666" />
                  <YAxis stroke="#666" tickFormatter={(val) => `$${val.toFixed(0)}`} />
                  <Tooltip formatter={(value) => `$${value.toFixed(2)}`} />
                  <Legend />
                  <Bar dataKey="total_pnl" fill="#667eea" name="Total P&L" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card className="stat-card">
            <CardContent>
              <Typography variant="h6" gutterBottom fontWeight="600">
                🎯 Win/Loss Distribution
              </Typography>
              <Typography variant="body2" color="text.secondary" mb={3}>
                Trade outcome breakdown
              </Typography>
              
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={winLossData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={(entry) => `${entry.name}: ${entry.value} (${((entry.value / summary.n_trades) * 100).toFixed(1)}%)`}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {winLossData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Session Stats Table */}
      <Card className="stat-card" sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom fontWeight="600">
            📈 Session Statistics
          </Typography>
          
          <TableContainer component={Paper} sx={{ mt: 2, boxShadow: 'none', border: '1px solid #e5e7eb' }}>
            <Table>
              <TableHead sx={{ background: '#f9fafb' }}>
                <TableRow>
                  <TableCell><strong>Session</strong></TableCell>
                  <TableCell align="right"><strong>Trades</strong></TableCell>
                  <TableCell align="right"><strong>Total P&L</strong></TableCell>
                  <TableCell align="right"><strong>Avg P&L</strong></TableCell>
                  <TableCell align="right"><strong>Win Rate</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {sessionData.map((row) => (
                  <TableRow key={row.session} hover>
                    <TableCell><strong>{row.session}</strong></TableCell>
                    <TableCell align="right">{row.trades}</TableCell>
                    <TableCell align="right" className={row.total_pnl > 0 ? 'positive' : 'negative'}>
                      ${row.total_pnl.toFixed(2)}
                    </TableCell>
                    <TableCell align="right">
                      ${(row.total_pnl / row.trades).toFixed(2)}
                    </TableCell>
                    <TableCell align="right">
                      {row.win_rate.toFixed(1)}%
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Recent Trades */}
      <Card className="stat-card">
        <CardContent>
          <Typography variant="h6" gutterBottom fontWeight="600">
            📋 Recent Trades (Last 20)
          </Typography>
          
          <TableContainer component={Paper} sx={{ mt: 2, boxShadow: 'none', border: '1px solid #e5e7eb' }}>
            <Table size="small">
              <TableHead sx={{ background: '#f9fafb' }}>
                <TableRow>
                  <TableCell><strong>Entry Time</strong></TableCell>
                  <TableCell><strong>Exit Time</strong></TableCell>
                  <TableCell align="right"><strong>Entry</strong></TableCell>
                  <TableCell align="right"><strong>Exit</strong></TableCell>
                  <TableCell align="center"><strong>Result</strong></TableCell>
                  <TableCell align="right"><strong>P&L</strong></TableCell>
                  <TableCell align="right"><strong>Return %</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {trades.slice(-20).reverse().map((trade, idx) => (
                  <TableRow key={idx} hover>
                    <TableCell>{new Date(trade.entry_time).toLocaleString()}</TableCell>
                    <TableCell>{new Date(trade.exit_time).toLocaleString()}</TableCell>
                    <TableCell align="right">${trade.entry_price.toFixed(2)}</TableCell>
                    <TableCell align="right">${trade.exit_price.toFixed(2)}</TableCell>
                    <TableCell align="center">
                      {trade.hit_tp ? (
                        <Chip label="TP" color="success" size="small" />
                      ) : trade.hit_sl ? (
                        <Chip label="SL" color="error" size="small" />
                      ) : (
                        <Chip label="TO" size="small" />
                      )}
                    </TableCell>
                    <TableCell align="right" className={trade.pnl_usd > 0 ? 'positive' : 'negative'}>
                      ${trade.pnl_usd.toFixed(2)}
                    </TableCell>
                    <TableCell align="right" className={trade.pnl_pct > 0 ? 'positive' : 'negative'}>
                      {(trade.pnl_pct * 100).toFixed(2)}%
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Box>
  );
}

export default BacktestResults;
