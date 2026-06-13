import { useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Button,
  Box,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive';
import NotificationsOffIcon from '@mui/icons-material/NotificationsOff';
import type { WatchlistItem, AssetType } from '@/types';

interface WatchlistWidgetProps {
  watchlist: WatchlistItem[];
  onAdd: (asset: AssetType) => void;
  onRemove: (id: string) => void;
  onToggleAlert: (id: string, enabled: boolean) => void;
  onSelectAsset?: (asset: AssetType) => void;
}

/**
 * WatchlistWidget Component
 * Manage and display user's watchlist
 */
export function WatchlistWidget({
  watchlist,
  onAdd,
  onRemove,
  onToggleAlert,
  onSelectAsset,
}: WatchlistWidgetProps) {
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [selectedAsset, setSelectedAsset] = useState<AssetType>('XAUUSD');

  const availableAssets: AssetType[] = ['XAUUSD', 'XAGUSD'];
  
  // Filter out already added assets
  const availableToAdd = availableAssets.filter(
    (asset) => !watchlist.some((item) => item.asset === asset)
  );

  const handleAdd = () => {
    onAdd(selectedAsset);
    setAddDialogOpen(false);
    setSelectedAsset('XAUUSD');
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  return (
    <>
      <Card elevation={3}>
        <CardContent>
          {/* Header */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6" fontWeight={600}>
              Watchlist
            </Typography>
            <Button
              startIcon={<AddIcon />}
              variant="outlined"
              size="small"
              onClick={() => setAddDialogOpen(true)}
              disabled={availableToAdd.length === 0}
            >
              Add
            </Button>
          </Box>

          {/* Watchlist Items */}
          {watchlist.length > 0 ? (
            <List dense>
              {watchlist.map((item) => (
                <ListItem
                  key={item.id}
                  sx={{
                    border: 1,
                    borderColor: 'divider',
                    borderRadius: 1,
                    mb: 1,
                    cursor: onSelectAsset ? 'pointer' : 'default',
                    '&:hover': onSelectAsset
                      ? {
                          bgcolor: 'action.hover',
                        }
                      : {},
                  }}
                  onClick={() => onSelectAsset?.(item.asset)}
                >
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="body1" fontWeight={600}>
                          {item.asset}
                        </Typography>
                        {item.alertEnabled && (
                          <Chip
                            icon={<NotificationsActiveIcon />}
                            label="Alert"
                            size="small"
                            color="primary"
                            sx={{ height: 20 }}
                          />
                        )}
                      </Box>
                    }
                    secondary={`Added ${formatDate(item.addedAt)}`}
                  />
                  <ListItemSecondaryAction>
                    <IconButton
                      edge="end"
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation();
                        onToggleAlert(item.id, !item.alertEnabled);
                      }}
                      sx={{ mr: 1 }}
                    >
                      {item.alertEnabled ? (
                        <NotificationsActiveIcon fontSize="small" color="primary" />
                      ) : (
                        <NotificationsOffIcon fontSize="small" />
                      )}
                    </IconButton>
                    <IconButton
                      edge="end"
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation();
                        onRemove(item.id);
                      }}
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </ListItemSecondaryAction>
                </ListItem>
              ))}
            </List>
          ) : (
            <Box sx={{ py: 4, textAlign: 'center' }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                No assets in watchlist
              </Typography>
              <Button
                startIcon={<AddIcon />}
                variant="outlined"
                size="small"
                onClick={() => setAddDialogOpen(true)}
                sx={{ mt: 1 }}
              >
                Add Your First Asset
              </Button>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Add Asset Dialog */}
      <Dialog open={addDialogOpen} onClose={() => setAddDialogOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Add to Watchlist</DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>Select Asset</InputLabel>
            <Select
              value={selectedAsset}
              label="Select Asset"
              onChange={(e) => setSelectedAsset(e.target.value as AssetType)}
            >
              {availableToAdd.map((asset) => (
                <MenuItem key={asset} value={asset}>
                  {asset}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleAdd} variant="contained">
            Add
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
