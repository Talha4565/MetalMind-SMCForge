import { Box, Card, CardContent, Typography, Chip, LinearProgress, Stack } from '@mui/material';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import TrendingFlatIcon from '@mui/icons-material/TrendingFlat';
import { getSignalColor } from '@/styles/theme';
import { useUiStore } from '@/store/uiStore';
import type { SignalType } from '@/types';

interface PredictionCardProps {
  asset: string;
  signal: SignalType;
  confidence: number;
  price: number;
  timestamp: string;
  isLoading?: boolean;
}

/**
 * PredictionCard Component
 * Displays latest trading prediction with signal and confidence
 */
export function PredictionCard({
  asset,
  signal,
  confidence,
  price,
  timestamp,
  isLoading = false,
}: PredictionCardProps) {
  const themeMode = useUiStore((state) => state.themeMode);
  const signalColor = getSignalColor(signal, themeMode);

  const getSignalIcon = () => {
    switch (signal) {
      case 'BUY':
        return <TrendingUpIcon sx={{ fontSize: 40 }} />;
      case 'SELL':
        return <TrendingDownIcon sx={{ fontSize: 40 }} />;
      case 'NEUTRAL':
        return <TrendingFlatIcon sx={{ fontSize: 40 }} />;
    }
  };

  const formatPrice = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  const formatTime = (isoString: string) => {
    return new Date(isoString).toLocaleString();
  };

  return (
    <Card
      elevation={3}
      sx={{
        position: 'relative',
        overflow: 'visible',
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 4,
          bgcolor: signalColor,
        },
      }}
    >
      <CardContent sx={{ pt: 3 }}>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" fontWeight={600}>
            {asset}
          </Typography>
          <Chip
            label={signal}
            sx={{
              bgcolor: signalColor,
              color: 'white',
              fontWeight: 600,
              fontSize: '0.875rem',
            }}
          />
        </Box>

        {/* Signal Icon & Price */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 3, mb: 3 }}>
          <Box
            sx={{
              width: 80,
              height: 80,
              borderRadius: 2,
              bgcolor: `${signalColor}20`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: signalColor,
            }}
          >
            {getSignalIcon()}
          </Box>
          <Box sx={{ flex: 1 }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Current Price
            </Typography>
            <Typography variant="h4" fontWeight={700}>
              {formatPrice(price)}
            </Typography>
          </Box>
        </Box>

        {/* Confidence */}
        <Box sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="body2" color="text.secondary">
              Confidence
            </Typography>
            <Typography variant="body2" fontWeight={600}>
              {confidence}%
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={confidence}
            sx={{
              height: 8,
              borderRadius: 4,
              bgcolor: `${signalColor}20`,
              '& .MuiLinearProgress-bar': {
                bgcolor: signalColor,
              },
            }}
          />
        </Box>

        {/* Timestamp */}
        <Typography variant="caption" color="text.secondary">
          Last updated: {formatTime(timestamp)}
        </Typography>

        {/* Loading Overlay */}
        {isLoading && (
          <Box
            sx={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              bgcolor: 'rgba(255, 255, 255, 0.8)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              backdropFilter: 'blur(2px)',
            }}
          >
            <Stack alignItems="center" spacing={1}>
              <LinearProgress sx={{ width: 120 }} />
              <Typography variant="caption">Updating...</Typography>
            </Stack>
          </Box>
        )}
      </CardContent>
    </Card>
  );
}
