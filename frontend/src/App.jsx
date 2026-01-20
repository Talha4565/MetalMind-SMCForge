import React, { useState } from 'react';
import { Container, Tabs, Tab, Box, Typography, AppBar, Toolbar } from '@mui/material';
import LivePredictions from './components/LivePredictions';
import BacktestResults from './components/BacktestResults';
import ShapAnalysis from './components/ShapAnalysis';
import ConfigurationPanel from './components/ConfigurationPanel';
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

  const handleConfigChange = (newConfig) => {
    setConfig(newConfig);
    console.log('Configuration updated:', newConfig);
    // TODO: Send to API to apply changes
  };

  return (
    <div className="App">
      <AppBar position="static" sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
        <Toolbar>
          <Typography variant="h5" component="div" sx={{ flexGrow: 1, fontWeight: 600 }}>
            🚀 ML Signals Dashboard
          </Typography>
          <Typography variant="body2" sx={{ opacity: 0.9 }}>
            XAU/USD • 15m • Enhanced Model
          </Typography>
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
          <LivePredictions />
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
