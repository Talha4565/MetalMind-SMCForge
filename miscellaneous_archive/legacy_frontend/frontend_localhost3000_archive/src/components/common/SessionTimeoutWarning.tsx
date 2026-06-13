import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  LinearProgress,
} from '@mui/material';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';

interface SessionTimeoutWarningProps {
  open: boolean;
  remainingTime: number;
  onStayLoggedIn: () => void;
  onLogout: () => void;
}

/**
 * SessionTimeoutWarning Component
 * Modal shown before auto-logout due to inactivity
 */
export function SessionTimeoutWarning({
  open,
  remainingTime,
  onStayLoggedIn,
  onLogout,
}: SessionTimeoutWarningProps) {
  const seconds = Math.floor(remainingTime / 1000);
  const progress = (remainingTime / 60000) * 100; // Assuming 1 min warning

  return (
    <Dialog
      open={open}
      onClose={onStayLoggedIn}
      maxWidth="sm"
      fullWidth
      disableEscapeKeyDown
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <WarningAmberIcon color="warning" />
          <Typography variant="h6">Session Timeout Warning</Typography>
        </Box>
      </DialogTitle>

      <DialogContent>
        <Typography variant="body1" gutterBottom>
          Your session is about to expire due to inactivity.
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          You will be automatically logged out in:
        </Typography>

        <Box sx={{ my: 3, textAlign: 'center' }}>
          <Typography variant="h3" color="warning.main" fontWeight={600}>
            {seconds}s
          </Typography>
          <LinearProgress
            variant="determinate"
            value={progress}
            color="warning"
            sx={{ mt: 2, height: 8, borderRadius: 4 }}
          />
        </Box>

        <Typography variant="body2" color="text.secondary">
          Click "Stay Logged In" to continue your session.
        </Typography>
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={onLogout} color="error" variant="outlined">
          Logout Now
        </Button>
        <Button onClick={onStayLoggedIn} variant="contained" autoFocus>
          Stay Logged In
        </Button>
      </DialogActions>
    </Dialog>
  );
}
