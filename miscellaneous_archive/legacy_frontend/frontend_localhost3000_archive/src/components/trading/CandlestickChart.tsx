import { useEffect, useRef } from 'react';
import { Box, Card, CardContent, Typography, ToggleButtonGroup, ToggleButton } from '@mui/material';
import { createChart, IChartApi, ISeriesApi, CandlestickData, Time } from 'lightweight-charts';
import { useUiStore } from '@/store/uiStore';
import { chartColors } from '@/styles/theme';

interface CandlestickChartProps {
  data: CandlestickData<Time>[];
  title?: string;
  height?: number;
  timeframe?: string;
  onTimeframeChange?: (timeframe: string) => void;
}

/**
 * CandlestickChart Component
 * Interactive trading chart using lightweight-charts
 */
export function CandlestickChart({
  data,
  title = 'Price Chart',
  height = 400,
  timeframe = '1H',
  onTimeframeChange,
}: CandlestickChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const themeMode = useUiStore((state) => state.themeMode);

  const timeframes = ['15M', '1H', '4H', '1D'];

  useEffect(() => {
    if (!chartContainerRef.current) return;

    const colors = chartColors[themeMode];

    // Create chart
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height,
      layout: {
        background: { color: colors.background },
        textColor: colors.text,
      },
      grid: {
        vertLines: { color: colors.grid },
        horzLines: { color: colors.grid },
      },
      crosshair: {
        mode: 1,
      },
      rightPriceScale: {
        borderColor: colors.grid,
      },
      timeScale: {
        borderColor: colors.grid,
        timeVisible: true,
        secondsVisible: false,
      },
    });

    chartRef.current = chart;

    // Add candlestick series
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: colors.candleUp,
      downColor: colors.candleDown,
      borderUpColor: colors.candleUp,
      borderDownColor: colors.candleDown,
      wickUpColor: colors.candleUp,
      wickDownColor: colors.candleDown,
    });

    seriesRef.current = candlestickSeries;

    // Set data
    if (data.length > 0) {
      candlestickSeries.setData(data);
      chart.timeScale().fitContent();
    }

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener('resize', handleResize);

    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [height, themeMode]);

  // Update data when it changes
  useEffect(() => {
    if (seriesRef.current && data.length > 0) {
      seriesRef.current.setData(data);
      chartRef.current?.timeScale().fitContent();
    }
  }, [data]);

  return (
    <Card elevation={3}>
      <CardContent>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" fontWeight={600}>
            {title}
          </Typography>
          
          {/* Timeframe Selector */}
          <ToggleButtonGroup
            value={timeframe}
            exclusive
            onChange={(_, value) => value && onTimeframeChange?.(value)}
            size="small"
          >
            {timeframes.map((tf) => (
              <ToggleButton key={tf} value={tf}>
                {tf}
              </ToggleButton>
            ))}
          </ToggleButtonGroup>
        </Box>

        {/* Chart Container */}
        <Box
          ref={chartContainerRef}
          sx={{
            position: 'relative',
            width: '100%',
            height: `${height}px`,
          }}
        />
      </CardContent>
    </Card>
  );
}
