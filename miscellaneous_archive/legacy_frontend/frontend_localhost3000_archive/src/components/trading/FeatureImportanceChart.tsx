import { Card, CardContent, Typography, Box } from '@mui/material';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { useUiStore } from '@/store/uiStore';
import type { FeatureImportance } from '@/types';

interface FeatureImportanceChartProps {
  data: FeatureImportance[];
  title?: string;
  maxFeatures?: number;
}

/**
 * FeatureImportanceChart Component
 * Displays SHAP feature importance values
 */
export function FeatureImportanceChart({
  data,
  title = 'Feature Importance (SHAP)',
  maxFeatures = 10,
}: FeatureImportanceChartProps) {
  const themeMode = useUiStore((state) => state.themeMode);
  
  // Get top N features
  const topFeatures = data
    .sort((a, b) => b.importance - a.importance)
    .slice(0, maxFeatures);

  // Color based on importance value
  const getColor = (importance: number) => {
    const maxImportance = Math.max(...topFeatures.map(f => f.importance));
    const normalized = importance / maxImportance;
    
    if (normalized > 0.7) return '#2e7d32'; // High importance - green
    if (normalized > 0.4) return '#1976d2'; // Medium importance - blue
    return '#757575'; // Low importance - gray
  };

  return (
    <Card elevation={3}>
      <CardContent>
        <Typography variant="h6" fontWeight={600} gutterBottom>
          {title}
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          Top {maxFeatures} most influential features for the prediction
        </Typography>

        {topFeatures.length > 0 ? (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart
              data={topFeatures}
              layout="vertical"
              margin={{ top: 5, right: 30, left: 120, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke={themeMode === 'dark' ? '#444' : '#ddd'} />
              <XAxis
                type="number"
                stroke={themeMode === 'dark' ? '#fff' : '#000'}
                style={{ fontSize: '0.875rem' }}
              />
              <YAxis
                type="category"
                dataKey="feature"
                stroke={themeMode === 'dark' ? '#fff' : '#000'}
                style={{ fontSize: '0.875rem' }}
                width={110}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: themeMode === 'dark' ? '#1e1e1e' : '#fff',
                  border: `1px solid ${themeMode === 'dark' ? '#444' : '#ddd'}`,
                  borderRadius: 4,
                }}
                labelStyle={{ color: themeMode === 'dark' ? '#fff' : '#000' }}
                formatter={(value: number) => [value.toFixed(4), 'Importance']}
              />
              <Bar dataKey="importance" radius={[0, 4, 4, 0]}>
                {topFeatures.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={getColor(entry.importance)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <Box sx={{ py: 4, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              No feature importance data available
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
}
