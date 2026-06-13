import { useState, useEffect } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  Button,
  Grid,
  ToggleButtonGroup,
  ToggleButton,
  IconButton,
} from '@mui/material';
import { useAuthStore } from '@/features/auth/store/authStore';
import { useTradingStore } from '@/features/trading/store/tradingStore';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import LogoutIcon from '@mui/icons-material/Logout';
import LightModeIcon from '@mui/icons-material/LightMode';
import DarkModeIcon from '@mui/icons-material/DarkMode';
import { useAuth } from '@/hooks/useAuth';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useUiStore } from '@/store/uiStore';
import {
  PredictionCard,
  CandlestickChart,
  FeatureImportanceChart,
  WatchlistWidget,
} from '@/components/trading';
import { WEBSOCKET_EVENTS } from '@/config/constants';
import type { AssetType, CandlestickData, Time } from '@/types';

// Mock data for demonstration (will be replaced with real data from backend)
const mockPrediction = {
  asset: 'XAUUSD',
  signal: 'BUY' as const,
  confidence: 85,
  price: 2050.32,
  timestamp: new Date().toISOString(),
};

const mockCandleData: CandlestickData<Time>[] = [
  { time: '2024-01-01' as Time, open: 2040, high: 2055, low: 2038, close: 2052 },
  { time: '2024-01-02' as Time, open: 2052, high: 2060, low: 2048, close: 2058 },
  { time: '2024-01-03' as Time, open: 2058, high: 2065, low: 2055, close: 2062 },
];

const mockFeatures = [
  { feature: 'RSI_14', importance: 0.15, rank: 1 },
  { feature: 'MACD', importance: 0.12, rank: 2 },
  { feature: 'EMA_50', importance: 0.10, rank: 3 },
  { feature: 'Volume', importance: 0.08, rank: 4 },
  { feature: 'Bollinger_Upper', importance: 0.07, rank: 5 },
];

export function Dashboard() {
  const user = useAuthStore((state) => state.user);
  const { logout } = useAuth();
  const { toggleTheme, themeMode } = useUiStore();
  
  const { selectedAsset, setSelectedAsset, watchlist, addToWatchlist, removeFromWatchlist, updateWatchlistItem } = useTradingStore();
  const [timeframe, setTimeframe] = useState('1H');

  // WebSocket connection
  const { subscribe, isConnected } = useWebSocket({
    autoConnect: true,
    onConnect: () => console.log('WebSocket connected'),
    onDisconnect: (reason) => console.log('WebSocket disconnected:', reason),
  });

  // Subscribe to prediction updates
  useEffect(() => {
    const unsubscribe = subscribe(WEBSOCKET_EVENTS.prediction, (data) => {
      console.log('Received prediction:', data);
      // Update trading store with real data
    });

    return unsubscribe;
  }, [subscribe]);

  return (
    <Container maxWidth="xl">
      <Box sx={{ py: 4 }}>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Box>
            <Typography variant="h3" gutterBottom>
              Trading Dashboard
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Welcome back, <strong>{user?.username}</strong>! • {isConnected ? '🟢 Live' : '🔴 Offline'}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <IconButton onClick={toggleTheme} color="primary">
              {themeMode === 'light' ? <DarkModeIcon /> : <LightModeIcon />}
            </IconButton>
            <Button
              component={RouterLink}
              to="/profile"
              variant="outlined"
              startIcon={<AccountCircleIcon />}
            >
              Profile
            </Button>
            <Button
              variant="outlined"
              color="error"
              startIcon={<LogoutIcon />}
              onClick={logout}
            >
              Logout
            </Button>
          </Box>
        </Box>

        {/* Asset Selector */}
        <Box sx={{ mb: 3 }}>
          <ToggleButtonGroup
            value={selectedAsset}
            exclusive
            onChange={(_, value) => value && setSelectedAsset(value)}
            size="large"
          >
            <ToggleButton value="XAUUSD">Gold (XAU/USD)</ToggleButton>
            <ToggleButton value="XAGUSD">Silver (XAG/USD)</ToggleButton>
          </ToggleButtonGroup>
        </Box>

        {/* Main Grid */}
        <Grid container spacing={3}>
          {/* Left Column - Prediction & Chart */}
          <Grid item xs={12} lg={8}>
            <Grid container spacing={3}>
              {/* Prediction Card */}
              <Grid item xs={12}>
                <PredictionCard
                  asset={selectedAsset}
                  signal={mockPrediction.signal}
                  confidence={mockPrediction.confidence}
                  price={mockPrediction.price}
                  timestamp={mockPrediction.timestamp}
                />
              </Grid>

              {/* Candlestick Chart */}
              <Grid item xs={12}>
                <CandlestickChart
                  data={mockCandleData}
                  title={`${selectedAsset} Price Chart`}
                  height={400}
                  timeframe={timeframe}
                  onTimeframeChange={setTimeframe}
                />
              </Grid>

              {/* Feature Importance */}
              <Grid item xs={12}>
                <FeatureImportanceChart data={mockFeatures} maxFeatures={10} />
              </Grid>
            </Grid>
          </Grid>

          {/* Right Column - Watchlist */}
          <Grid item xs={12} lg={4}>
            <WatchlistWidget
              watchlist={watchlist}
              onAdd={(asset) => addToWatchlist({
                id: Date.now().toString(),
                asset,
                alertEnabled: false,
                addedAt: new Date().toISOString(),
              })}
              onRemove={removeFromWatchlist}
              onToggleAlert={(id, enabled) => updateWatchlistItem(id, { alertEnabled: enabled })}
              onSelectAsset={setSelectedAsset}
            />
          </Grid>
        </Grid>
      </Box>
    </Container>
  );
}
