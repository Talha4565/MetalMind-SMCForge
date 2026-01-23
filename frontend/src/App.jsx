import React, { useState, useEffect } from 'react';
import { Container, Tabs, Tab, Box, Typography, AppBar, Toolbar, IconButton, Menu, MenuItem } from '@mui/material';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import LivePredictions from './components/LivePredictions';
import BacktestResults from './components/BacktestResults';
import ShapAnalysis from './components/ShapAnalysis';
import ConfigurationPanel from './components/ConfigurationPanel';
import Login from './components/Login';
import './App.css';

function TabPanel({ children, value, index }) {
  return (
    <div hidden={value !== index} style={{ padding: '24px 0' }}>
      {value === index && children}
    </div>
  );
}

function App() {
  const [activeTab, setActiveTab] = useState(0);
  const [config, setConfig] = useState({});
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userEmail, setUserEmail] = useState('');
  const [selectedAsset, setSelectedAsset] = useState('gold');
  const [anchorEl, setAnchorEl] = useState(null);

  // Check if user is already logged in
  useEffect(() => {
    const token = localStorage.getItem('token');
    const email = localStorage.getItem('user_email');
    
    // Validate token format (JWT should start with eyJ)
    if (token && email && token.startsWith('eyJ')) {
      console.log('Valid token found, logging in automatically');
      setIsAuthenticated(true);
      setUserEmail(email);
    } else if (token || email) {
      // Clear invalid/old tokens
      console.log('Invalid token detected, clearing storage');
      localStorage.clear();
    }
  }, []);

  const handleLogin = (token, email) => {
    setIsAuthenticated(true);
    setUserEmail(email);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user_email');
    setIsAuthenticated(false);
    setUserEmail('');
    setAnchorEl(null);
  };

  const handleConfigChange = async (newConfig) => {
    setConfig(newConfig);
    console.log('Configuration updated:', newConfig);
    
    // Send to API to save changes
    try {
      const axios = (await import('./utils/axios')).default;
      await axios.post('/config', newConfig);
      console.log('Configuration saved to server');
    } catch (error) {
      console.error('Failed to save configuration:', error);
    }
  };

  // Show login page if not authenticated
  if (!isAuthenticated) {
    return <Login onLoginSuccess={handleLogin} />;
  }

  return (
    <div className="App">
      <AppBar position="static" sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
        <Toolbar>
          <Typography variant="h5" component="div" sx={{ flexGrow: 1, fontWeight: 600 }}>
            🚀 ML Signals Dashboard
          </Typography>
          <Typography variant="body2" sx={{ opacity: 0.9, mr: 2 }}>
            {selectedAsset === 'gold' ? '🥇 XAU/USD' : '🥈 XAG/USD'} • 15m • Enhanced Model
          </Typography>
          <IconButton
            color="inherit"
            onClick={(e) => setAnchorEl(e.currentTarget)}
            sx={{ ml: 1 }}
          >
            <AccountCircleIcon />
          </IconButton>
          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={() => setAnchorEl(null)}
          >
            <MenuItem disabled>
              <Typography variant="body2" color="text.secondary">
                {userEmail}
              </Typography>
            </MenuItem>
            <MenuItem onClick={handleLogout}>Logout</MenuItem>
          </Menu>
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ mt: 3 }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs 
            value={activeTab} 
            onChange={(e, newValue) => setActiveTab(newValue)}
            variant="fullWidth"
            sx={{ 
              '& .MuiTab-root': { 
                fontSize: '1rem',
                fontWeight: 500,
                textTransform: 'none'
              }
            }}
          >
            <Tab label="📈 Live Predictions" />
            <Tab label="💰 Backtest Results" />
            <Tab label="🔍 SHAP Analysis" />
            <Tab label="⚙️ Configuration" />
          </Tabs>
        </Box>

        <TabPanel value={activeTab} index={0}>
          <LivePredictions onAssetChange={setSelectedAsset} />
        </TabPanel>

        <TabPanel value={activeTab} index={1}>
          <BacktestResults />
        </TabPanel>

        <TabPanel value={activeTab} index={2}>
          <ShapAnalysis />
        </TabPanel>

        <TabPanel value={activeTab} index={3}>
          <ConfigurationPanel onConfigChange={handleConfigChange} />
        </TabPanel>
      </Container>
    </div>
  );
}

export default App;
