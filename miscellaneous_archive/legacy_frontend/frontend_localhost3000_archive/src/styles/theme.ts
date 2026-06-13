import { createTheme, ThemeOptions, alpha } from '@mui/material/styles';

/**
 * Color Palette
 */
const colors = {
  primary: {
    main: '#1976d2',
    light: '#42a5f5',
    dark: '#1565c0',
    contrastText: '#ffffff',
  },
  success: {
    main: '#2e7d32',
    light: '#4caf50',
    dark: '#1b5e20',
    contrastText: '#ffffff',
  },
  error: {
    main: '#d32f2f',
    light: '#ef5350',
    dark: '#c62828',
    contrastText: '#ffffff',
  },
  warning: {
    main: '#ed6c02',
    light: '#ff9800',
    dark: '#e65100',
    contrastText: '#ffffff',
  },
  info: {
    main: '#0288d1',
    light: '#03a9f4',
    dark: '#01579b',
    contrastText: '#ffffff',
  },
};

/**
 * Common theme options
 */
const commonTheme: ThemeOptions = {
  typography: {
    fontFamily: [
      'Roboto',
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
    ].join(','),
    
    // Headings
    h1: {
      fontSize: '2.5rem',
      fontWeight: 700,
      lineHeight: 1.2,
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 700,
      lineHeight: 1.3,
    },
    h3: {
      fontSize: '1.75rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    h4: {
      fontSize: '1.5rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    h5: {
      fontSize: '1.25rem',
      fontWeight: 500,
      lineHeight: 1.5,
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 500,
      lineHeight: 1.6,
    },
    
    // Body text
    body1: {
      fontSize: '1rem',
      lineHeight: 1.5,
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.43,
    },
    
    // Buttons
    button: {
      textTransform: 'none',
      fontWeight: 500,
    },
  },
  
  shape: {
    borderRadius: 8,
  },
  
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: '8px 16px',
          fontSize: '0.875rem',
        },
        sizeLarge: {
          padding: '12px 24px',
          fontSize: '1rem',
        },
        sizeSmall: {
          padding: '4px 10px',
          fontSize: '0.8125rem',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        rounded: {
          borderRadius: 12,
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 6,
        },
      },
    },
  },
};

/**
 * Light Theme
 */
export const lightTheme = createTheme({
  ...commonTheme,
  palette: {
    mode: 'light',
    ...colors,
    background: {
      default: '#f5f5f5',
      paper: '#ffffff',
    },
    text: {
      primary: 'rgba(0, 0, 0, 0.87)',
      secondary: 'rgba(0, 0, 0, 0.6)',
      disabled: 'rgba(0, 0, 0, 0.38)',
    },
    divider: 'rgba(0, 0, 0, 0.12)',
  },
  components: {
    ...commonTheme.components,
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#ffffff',
          color: 'rgba(0, 0, 0, 0.87)',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.12)',
        },
      },
    },
  },
});

/**
 * Dark Theme
 */
export const darkTheme = createTheme({
  ...commonTheme,
  palette: {
    mode: 'dark',
    ...colors,
    background: {
      default: '#121212',
      paper: '#1e1e1e',
    },
    text: {
      primary: '#ffffff',
      secondary: 'rgba(255, 255, 255, 0.7)',
      disabled: 'rgba(255, 255, 255, 0.5)',
    },
    divider: 'rgba(255, 255, 255, 0.12)',
  },
  components: {
    ...commonTheme.components,
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#1e1e1e',
          color: '#ffffff',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.3)',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
      },
    },
  },
});

/**
 * Trading-specific colors helper
 */
export const tradingColors = {
  buy: colors.success.main,
  sell: colors.error.main,
  neutral: '#757575',
  
  getBuyColor: (theme: 'light' | 'dark') => 
    theme === 'light' ? colors.success.main : colors.success.light,
  
  getSellColor: (theme: 'light' | 'dark') => 
    theme === 'light' ? colors.error.main : colors.error.light,
  
  getNeutralColor: (theme: 'light' | 'dark') => 
    theme === 'light' ? '#757575' : '#9e9e9e',
};

/**
 * Helper to get signal color
 */
export function getSignalColor(signal: 'BUY' | 'SELL' | 'NEUTRAL', mode: 'light' | 'dark' = 'light') {
  switch (signal) {
    case 'BUY':
      return tradingColors.getBuyColor(mode);
    case 'SELL':
      return tradingColors.getSellColor(mode);
    case 'NEUTRAL':
      return tradingColors.getNeutralColor(mode);
    default:
      return tradingColors.neutral;
  }
}

/**
 * Chart theme colors
 */
export const chartColors = {
  light: {
    grid: 'rgba(0, 0, 0, 0.1)',
    text: 'rgba(0, 0, 0, 0.87)',
    background: '#ffffff',
    candleUp: colors.success.main,
    candleDown: colors.error.main,
  },
  dark: {
    grid: 'rgba(255, 255, 255, 0.1)',
    text: 'rgba(255, 255, 255, 0.87)',
    background: '#1e1e1e',
    candleUp: colors.success.light,
    candleDown: colors.error.light,
  },
};
